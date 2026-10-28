<template>
  <div>
    <div class="toolbar">
      <el-button type="primary" @click="openCreate">发起评审</el-button>
      <el-button @click="$router.push('/projects')">返回</el-button>
    </div>

    <el-table :data="reviews" v-loading="loading" border>
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column prop="title" label="评审标题" />
      <el-table-column label="状态" width="110">
        <template #default="{ row }">
          <el-tag :type="statusType(row.status)">{{ statusText(row.status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="用例数" width="90">
        <template #default="{ row }">{{ row.case_ids.length }}</template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="180" />
      <el-table-column label="操作" width="230">
        <template #default="{ row }">
          <el-button link type="primary" @click="openDetail(row)">查看</el-button>
          <el-button link type="warning" @click="changeStatus(row, 3)">标记完成</el-button>
          <el-button link type="danger" @click="onDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 新建 -->
    <el-dialog v-model="dialogVisible" title="发起评审" width="620">
      <el-form :model="form" label-width="90">
        <el-form-item label="标题" required>
          <el-input v-model="form.title" />
        </el-form-item>
        <el-form-item label="评审用例">
          <el-select v-model="form.case_ids" multiple filterable style="width:100%"
                     placeholder="选择用例">
            <el-option v-for="c in cases" :key="c.id" :value="c.id"
                       :label="`${c.case_no} - ${c.title}`" />
          </el-select>
        </el-form-item>
        <el-form-item label="评审人ID">
          <el-select v-model="form.reviewer_ids" multiple style="width:100%"
                     placeholder="填写用户ID（暂时手填）">
            <el-option v-for="u in [1, 2, 3]" :key="u" :value="u" :label="`用户${u}`" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="onCreate">确定</el-button>
      </template>
    </el-dialog>

    <!-- 详情 -->
    <el-drawer v-model="detailVisible" title="评审详情" size="640">
      <div v-if="current">
        <h3>{{ current.title }}</h3>
        <p>状态：<el-tag :type="statusType(current.status)">{{ statusText(current.status) }}</el-tag></p>
        <h4>用例</h4>
        <el-table :data="current.cases" size="small" border>
          <el-table-column prop="case_no" label="编号" width="110" />
          <el-table-column prop="title" label="标题" />
        </el-table>

        <h4 style="margin-top:16px">提交评审意见</h4>
        <el-form :inline="true">
          <el-form-item>
            <el-select v-model="comment.case_id" placeholder="选择用例" style="width:220px">
              <el-option v-for="c in current.cases" :key="c.id" :value="c.id"
                         :label="`${c.case_no} - ${c.title}`" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-select v-model="comment.result" style="width:120px">
              <el-option :value="1" label="通过" />
              <el-option :value="2" label="拒绝" />
              <el-option :value="3" label="建议" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-input v-model="comment.content" placeholder="意见内容" style="width:220px" />
          </el-form-item>
          <el-button type="primary" @click="submitComment">提交</el-button>
        </el-form>

        <h4>评审意见记录</h4>
        <el-timeline>
          <el-timeline-item v-for="c in current.comments" :key="c.id"
                            :timestamp="c.created_at">
            <b>{{ { 1: '通过', 2: '拒绝', 3: '建议' }[c.result] }}</b> - {{ c.content }}
          </el-timeline-item>
        </el-timeline>
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/utils/request'

const route = useRoute()
const pid = route.params.id

const reviews = ref([])
const cases = ref([])
const loading = ref(false)

const dialogVisible = ref(false)
const form = reactive({ title: '', case_ids: [], reviewer_ids: [] })

const detailVisible = ref(false)
const current = ref(null)
const comment = reactive({ case_id: null, result: 1, content: '' })

function statusText(s) { return { 1: '待评审', 2: '评审中', 3: '已完成', 4: '取消' }[s] }
function statusType(s) { return { 1: 'info', 2: 'warning', 3: 'success', 4: 'danger' }[s] }

async function load() {
  loading.value = true
  try { reviews.value = await api.get(`/projects/${pid}/reviews`) }
  finally { loading.value = false }
}

async function loadCases() {
  const data = await api.get(`/projects/${pid}/cases`, { params: { page: 1, size: 200 } })
  cases.value = data.items
}

function openCreate() {
  form.title = ''
  form.case_ids = []
  form.reviewer_ids = []
  dialogVisible.value = true
}

async function onCreate() {
  if (!form.title) return ElMessage.warning('标题必填')
  await api.post(`/projects/${pid}/reviews`, form)
  ElMessage.success('已发起')
  dialogVisible.value = false
  load()
}

async function openDetail(row) {
  current.value = await api.get(`/projects/${pid}/reviews/${row.id}`)
  detailVisible.value = true
}

async function submitComment() {
  if (!comment.case_id) return ElMessage.warning('请选择用例')
  await api.post(`/projects/${pid}/reviews/${current.value.id}/comments`, comment)
  ElMessage.success('已提交')
  comment.content = ''
  openDetail(current.value)
}

async function changeStatus(row, status) {
  await api.put(`/projects/${pid}/reviews/${row.id}/status`, { status })
  ElMessage.success('已更新')
  load()
}

async function onDelete(row) {
  await ElMessageBox.confirm('确认删除该评审？', '提示', { type: 'warning' })
  await api.delete(`/projects/${pid}/reviews/${row.id}`)
  ElMessage.success('已删除')
  load()
}

onMounted(() => { load(); loadCases() })
</script>

<style scoped>
.toolbar { display: flex; gap: 8px; margin-bottom: 12px; }
</style>