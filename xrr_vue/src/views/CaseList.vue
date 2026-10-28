<template>
  <div>
    <div class="toolbar">
  <el-input v-model="query.keyword" placeholder="搜索标题/编号" style="width:220px"
            clearable @keyup.enter="load" />
  <el-select v-model="query.priority" placeholder="优先级" clearable style="width:110px">
    <el-option :value="1" label="P0" />
    <el-option :value="2" label="P1" />
    <el-option :value="3" label="P2" />
    <el-option :value="4" label="P3" />
  </el-select>
  <el-button type="primary" @click="load">查询</el-button>
  <el-button type="success" @click="openCreate">新建用例</el-button>

  <el-upload :show-file-list="false" :before-upload="onImport" accept=".xlsx,.xls" style="display:inline-block">
    <el-button>导入 Excel</el-button>
  </el-upload>
  <el-button @click="onExport">导出 Excel</el-button>

  <el-upload :show-file-list="false" :before-upload="onImportXmind" accept=".xmind" style="display:inline-block">
    <el-button type="warning">导入 XMind</el-button>
  </el-upload>
  <el-button link @click="showXmindTips">脑图规范?</el-button>

  <el-button @click="$router.push('/projects')">返回</el-button>
</div>

    <el-table :data="cases" v-loading="loading" border>
      <el-table-column prop="case_no" label="编号" width="110" />
      <el-table-column prop="title" label="标题" />
      <el-table-column label="优先级" width="90">
        <template #default="{ row }">P{{ row.priority - 1 }}</template>
      </el-table-column>
      <el-table-column prop="case_type" label="类型" width="100" />
      <el-table-column prop="current_version" label="版本" width="70" />
      <el-table-column prop="updated_at" label="更新时间" width="170" />
      <el-table-column label="操作" width="280">
        <template #default="{ row }">
          <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
          <el-button link type="primary" @click="showVersions(row)">版本</el-button>
          <el-button link type="primary" @click="openAttach(row)">附件</el-button>
          <el-button link type="danger" @click="onDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination
      style="margin-top:12px; justify-content:flex-end"
      layout="total, prev, pager, next"
      :total="total"
      :page-size="query.size"
      :current-page="query.page"
      @current-change="p => { query.page = p; load() }"
    />

    <!-- 用例编辑弹窗 -->
    <el-dialog v-model="dialogVisible" :title="editing ? '编辑用例' : '新建用例'" width="640">
      <el-form :model="form" label-width="80">
        <el-form-item label="标题" required>
          <el-input v-model="form.title" />
        </el-form-item>
        <el-form-item label="前置条件">
          <el-input v-model="form.precondition" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="步骤">
          <div style="width:100%">
            <div v-for="(s, i) in form.steps" :key="i" class="step-row">
              <el-input v-model="s.step" placeholder="步骤" style="flex:1" />
              <el-input v-model="s.expect" placeholder="预期" style="flex:1" />
              <el-button link type="danger" @click="form.steps.splice(i, 1)">删除</el-button>
            </div>
            <el-button link type="primary" @click="form.steps.push({ step: '', expect: '' })">
              + 添加步骤
            </el-button>
          </div>
        </el-form-item>
        <el-form-item label="优先级">
          <el-select v-model="form.priority">
            <el-option :value="1" label="P0" />
            <el-option :value="2" label="P1" />
            <el-option :value="3" label="P2" />
            <el-option :value="4" label="P3" />
          </el-select>
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="form.case_type">
            <el-option value="functional" label="功能" />
            <el-option value="api" label="接口" />
            <el-option value="performance" label="性能" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="onSave">保存</el-button>
      </template>
    </el-dialog>

    <!-- 版本抽屉 -->
    <el-drawer v-model="versionVisible" title="版本历史" size="480">
      <el-timeline>
        <el-timeline-item v-for="v in versions" :key="v.id"
                          :timestamp="v.created_at" placement="top">
          <div>v{{ v.version }} — {{ v.change_log }}</div>
          <div style="color:#666;font-size:12px">{{ v.snapshot?.title }}</div>
        </el-timeline-item>
      </el-timeline>
    </el-drawer>

    <!-- 附件抽屉 -->
    <el-drawer v-model="attachVisible" title="用例附件" size="480">
      <el-upload :show-file-list="false" :http-request="uploadAttach">
        <el-button type="primary">上传附件</el-button>
      </el-upload>
      <el-divider />
      <el-table :data="attachments" size="small">
        <el-table-column prop="file_name" label="文件名" />
        <el-table-column label="大小(KB)" width="100">
          <template #default="{ row }">{{ Math.round(row.file_size / 1024) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="150">
          <template #default="{ row }">
            <el-button link type="primary" @click="downloadAttach(row)">下载</el-button>
            <el-button link type="danger" @click="removeAttach(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
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

const cases = ref([])
const total = ref(0)
const loading = ref(false)
const query = reactive({ page: 1, size: 20, keyword: '', priority: null })

const dialogVisible = ref(false)
const editing = ref(false)
const editingId = ref(null)
const form = reactive({
  title: '', precondition: '', steps: [], priority: 2, case_type: 'functional'
})

const versionVisible = ref(false)
const versions = ref([])

const attachVisible = ref(false)
const attachCaseId = ref(null)
const attachments = ref([])

async function load() {
  loading.value = true
  try {
    const params = { page: query.page, size: query.size }
    if (query.keyword) params.keyword = query.keyword
    if (query.priority) params.priority = query.priority
    const data = await api.get(`/projects/${pid}/cases`, { params })
    cases.value = data.items
    total.value = data.total
  } finally { loading.value = false }
}

function openCreate() {
  editing.value = false
  editingId.value = null
  Object.assign(form, {
    title: '', precondition: '',
    steps: [{ step: '', expect: '' }], priority: 2, case_type: 'functional'
  })
  dialogVisible.value = true
}

async function openEdit(row) {
  const detail = await api.get(`/projects/${pid}/cases/${row.id}`)
  editing.value = true
  editingId.value = row.id
  Object.assign(form, {
    title: detail.title,
    precondition: detail.precondition || '',
    steps: detail.steps?.length ? detail.steps : [{ step: '', expect: '' }],
    priority: detail.priority,
    case_type: detail.case_type,
  })
  dialogVisible.value = true
}

async function onSave() {
  if (!form.title) return ElMessage.warning('标题必填')
  if (editing.value) {
    await api.put(`/projects/${pid}/cases/${editingId.value}`, form)
  } else {
    await api.post(`/projects/${pid}/cases`, form)
  }
  ElMessage.success('保存成功')
  dialogVisible.value = false
  load()
}

async function onDelete(row) {
  await ElMessageBox.confirm(`确认删除用例「${row.title}」？`, '提示', { type: 'warning' })
  await api.delete(`/projects/${pid}/cases/${row.id}`)
  ElMessage.success('已删除')
  load()
}

async function showVersions(row) {
  versions.value = await api.get(`/projects/${pid}/cases/${row.id}/versions`)
  versionVisible.value = true
}

/* ---------- Excel ---------- */
async function onExport() {
  const token = localStorage.getItem('access_token')
  const url = `/api/projects/${pid}/cases/export`
  const res = await fetch(url, { headers: { Authorization: `Bearer ${token}` } })
  if (!res.ok) return ElMessage.error('导出失败')
  const blob = await res.blob()
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = `cases_project_${pid}.xlsx`
  a.click()
  URL.revokeObjectURL(a.href)
}

async function onImport(file) {
  const fd = new FormData()
  fd.append('file', file)
  const token = localStorage.getItem('access_token')
  const res = await fetch(`/api/projects/${pid}/cases/import`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
    body: fd,
  })
  const data = await res.json()
  if (data.code === 0) {
    ElMessage.success(`导入成功 ${data.data.success} 条`)
    if (data.data.errors?.length) {
      console.warn('导入错误:', data.data.errors)
    }
    load()
  } else {
    ElMessage.error(data.msg)
  }
  return false
}

/* ---------- 附件 ---------- */
async function openAttach(row) {
  attachCaseId.value = row.id
  attachVisible.value = true
  await loadAttachments()
}

async function loadAttachments() {
  attachments.value = await api.get('/files', {
    params: { biz_type: 'case', biz_id: attachCaseId.value }
  })
}

/* ---------- XMind ---------- */
async function onImportXmind(file) {
  const fd = new FormData()
  fd.append('file', file)
  const token = localStorage.getItem('access_token')
  const res = await fetch(`/api/projects/${pid}/cases/import-xmind`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
    body: fd,
  })
  const data = await res.json()
  if (data.code === 0) {
    const { success, modules_created, errors } = data.data
    ElMessage.success(`XMind 导入成功 ${success} 条，新增模块 ${modules_created} 个`)
    if (errors?.length) {
      console.warn('XMind 导入部分失败:', errors)
      ElMessage.warning(`有 ${errors.length} 条失败，详情见控制台`)
    }
    load()
  } else {
    ElMessage.error(data.msg)
  }
  return false
}

async function showXmindTips() {
  const tips = await api.get(`/projects/${pid}/cases/import-xmind/template-tips`)
  const html = `
    <div style="line-height:1.8">
      <b>层级约定</b>
      <ul>${tips.levels.map(t => `<li>${t}</li>`).join('')}</ul>
      <b>兼容规则</b>
      <ul>${tips.compat.map(t => `<li>${t}</li>`).join('')}</ul>
    </div>`
  ElMessageBox.alert(html, 'XMind 结构规范', {
    dangerouslyUseHTMLString: true,
    confirmButtonText: '知道了',
  })
}

async function uploadAttach({ file }) {
  const fd = new FormData()
  fd.append('file', file)
  fd.append('biz_type', 'case')
  fd.append('biz_id', attachCaseId.value)
  const token = localStorage.getItem('access_token')
  const res = await fetch('/api/files/upload', {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
    body: fd,
  })
  const data = await res.json()
  if (data.code === 0) {
    ElMessage.success('上传成功')
    loadAttachments()
  } else {
    ElMessage.error(data.msg)
  }
}

function downloadAttach(row) {
  window.open(`/api/files/${row.id}`, '_blank')
}

async function removeAttach(row) {
  await ElMessageBox.confirm('确认删除该附件？', '提示', { type: 'warning' })
  await api.delete(`/files/${row.id}`)
  ElMessage.success('已删除')
  loadAttachments()
}

onMounted(load)
</script>

<style scoped>
.toolbar { display: flex; gap: 8px; margin-bottom: 12px; flex-wrap: wrap; }
.step-row { display: flex; gap: 8px; margin-bottom: 8px; align-items: center; }
</style>