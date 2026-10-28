<template>
  <div>
    <div class="toolbar">
      <el-button type="primary" @click="dialogVisible = true">新建项目</el-button>
    </div>
    <el-table :data="projects" v-loading="loading" border>
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column prop="name" label="项目名称" />
      <el-table-column prop="code" label="编码" width="130" />
      <el-table-column prop="description" label="描述" />
      <el-table-column prop="created_at" label="创建时间" width="180" />
      <el-table-column label="操作" width="200">
        <template #default="{ row }">
          <el-button link type="primary" @click="$router.push(`/projects/${row.id}/cases`)">
            用例管理
          </el-button>
          <el-button link type="danger" @click="onDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" title="新建项目" width="480">
      <el-form :model="form" label-width="80">
        <el-form-item label="项目名" required>
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="编码" required>
          <el-input v-model="form.code" placeholder="唯一，如 PROJ-001" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="onCreate">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/utils/request'

const projects = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const form = reactive({ name: '', code: '', description: '' })

async function load() {
  loading.value = true
  try { projects.value = await api.get('/projects') }
  finally { loading.value = false }
}

async function onCreate() {
  if (!form.name || !form.code) return ElMessage.warning('请填写必填项')
  await api.post('/projects', form)
  ElMessage.success('创建成功')
  dialogVisible.value = false
  Object.assign(form, { name: '', code: '', description: '' })
  load()
}

async function onDelete(row) {
  await ElMessageBox.confirm(`确认删除项目「${row.name}」？`, '提示', { type: 'warning' })
  await api.delete(`/projects/${row.id}`)
  ElMessage.success('已删除')
  load()
}

onMounted(load)
</script>

<style scoped>
.toolbar { margin-bottom: 12px; }
</style>