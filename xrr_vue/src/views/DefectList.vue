<template>
  <div>
    <div class="toolbar">
      <el-button type="primary" @click="openCreate">新建缺陷</el-button>
      <el-select v-model="filter.status" placeholder="状态" clearable style="width:130px" @change="load">
        <el-option :value="1" label="新建" />
        <el-option :value="2" label="处理中" />
        <el-option :value="3" label="已解决" />
        <el-option :value="4" label="关闭" />
      </el-select>
      <el-select v-model="filter.severity" placeholder="严重程度" clearable style="width:130px" @change="load">
        <el-option :value="1" label="致命" />
        <el-option :value="2" label="严重" />
        <el-option :value="3" label="一般" />
        <el-option :value="4" label="轻微" />
      </el-select>
      <el-button @click="$router.push('/projects')">返回</el-button>
    </div>

    <el-table :data="defects" v-loading="loading" border>
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column prop="title" label="标题" />
      <el-table-column label="严重程度" width="110">
        <template #default="{ row }">
          <el-tag :type="severityType(row.severity)">{{ severityText(row.severity) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="110">
        <template #default="{ row }">
          <el-tag :type="statusType(row.status)">{{ statusText(row.status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="180" />
      <el-table-column label="操作" width="180">
        <template #default="{ row }">
          <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
          <el-button link type="danger" @click="onDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" :title="editing ? '编辑缺陷' : '新建缺陷'" width="560">
      <el-form :model="form" label-width="90">
        <el-form-item label="标题" required>
          <el-input v-model="form.title" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="严重程度">
          <el-select v-model="form.severity" style="width:100%">
            <el-option :value="1" label="致命" />
            <el-option :value="2" label="严重" />
            <el-option :value="3" label="一般" />
            <el-option :value="4" label="轻微" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="form.status" style="width:100%">
            <el-option :value="1" label="新建" />
            <el-option :value="2" label="处理中" />
            <el-option :value="3" label="已解决" />
            <el-option :value="4" label="关闭" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="onSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/utils/request'

const route = useRoute()
const pid = route.params.id

const defects = ref([])
const loading = ref(false)
const filter = reactive({ status: null, severity: null })

const dialogVisible = ref(false)
const editing = ref(false)
const editingId = ref(null)
const form = reactive({ title: '', description: '', severity: 2, status: 1 })

const severityText = s => ({ 1: '致命', 2: '严重', 3: '一般', 4: '轻微' }[s])
const severityType = s => ({ 1: 'danger', 2: 'warning', 3: 'info', 4: 'success' }[s])
const statusText = s => ({ 1: '新建', 2: '处理中', 3: '已解决', 4: '关闭' }[s])
const statusType = s => ({ 1: 'danger', 2: 'warning', 3: 'success', 4: 'info' }[s])

async function load() {
  loading.value = true
  try {
    const params = {}
    if (filter.status) params.status = filter.status
    if (filter.severity) params.severity = filter.severity
    defects.value = await api.get(`/projects/${pid}/defects`, { params })
  } finally { loading.value = false }
}

function openCreate() {
  editing.value = false
  editingId.value = null
  Object.assign(form, { title: '', description: '', severity: 2, status: 1 })
  dialogVisible.value = true
}

function openEdit(row) {
  editing.value = true
  editingId.value = row.id
  Object.assign(form, row)
  dialogVisible.value = true
}

async function onSave() {
  if (!form.title) return ElMessage.warning('标题必填')
  if (editing.value) {
    await api.put(`/projects/${pid}/defects/${editingId.value}`, form)
  } else {
    await api.post(`/projects/${pid}/defects`, form)
  }
  ElMessage.success('已保存')
  dialogVisible.value = false
  load()
}

async function onDelete(row) {
  await ElMessageBox.confirm('确认删除该缺陷？', '提示', { type: 'warning' })
  await api.delete(`/projects/${pid}/defects/${row.id}`)
  ElMessage.success('已删除')
  load()
}

onMounted(load)
</script>

<style scoped>
.toolbar { display: flex; gap: 8px; margin-bottom: 12px; }
</style>