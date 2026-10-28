<template>
  <div v-loading="loading">
    <div class="toolbar">
      <el-button @click="$router.push('/projects')">返回</el-button>
    </div>

    <el-row :gutter="16">
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-title">用例总数</div>
          <div class="stat-value">{{ data.total_cases }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-title">缺陷总数</div>
          <div class="stat-value">{{ data.total_defects }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-title">执行通过率</div>
          <div class="stat-value">{{ data.pass_rate }}%</div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16" style="margin-top:16px">
      <el-col :span="8">
        <el-card header="优先级分布">
          <div v-for="(v, k) in data.priority_dist" :key="k" class="bar-row">
            <span class="label">{{ k }}</span>
            <el-progress :percentage="pct(v, data.total_cases)" :stroke-width="14" style="flex:1" />
            <span class="val">{{ v }}</span>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card header="执行结果分布">
          <div v-for="(v, k) in data.execution_dist" :key="k" class="bar-row">
            <span class="label">{{ k }}</span>
            <el-progress :percentage="pct(v, Object.values(data.execution_dist).reduce((a,b)=>a+b,0))"
                         :stroke-width="14" :color="execColor(k)" style="flex:1" />
            <span class="val">{{ v }}</span>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card header="缺陷严重程度分布">
          <div v-for="(v, k) in data.defect_dist" :key="k" class="bar-row">
            <span class="label">{{ k }}</span>
            <el-progress :percentage="pct(v, data.total_defects)" :stroke-width="14" status="exception" style="flex:1" />
            <span class="val">{{ v }}</span>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import api from '@/utils/request'

const route = useRoute()
const pid = route.params.id
const loading = ref(false)
const data = ref({
  total_cases: 0, total_defects: 0, pass_rate: 0,
  priority_dist: {}, execution_dist: {}, defect_dist: {}
})

function pct(v, total) {
  if (!total) return 0
  return Math.round((v / total) * 100)
}

function execColor(k) {
  return { '通过': '#67C23A', '失败': '#F56C6C', '阻塞': '#E6A23C', '跳过': '#909399' }[k] || '#409EFF'
}

async function load() {
  loading.value = true
  try { data.value = await api.get(`/projects/${pid}/reports/overview`) }
  finally { loading.value = false }
}

onMounted(load)
</script>

<style scoped>
.toolbar { margin-bottom: 12px; }
.stat-title { color: #909399; font-size: 14px; }
.stat-value { font-size: 30px; font-weight: bold; margin-top: 6px; color: #303133; }
.bar-row { display: flex; align-items: center; gap: 8px; margin: 8px 0; }
.bar-row .label { width: 48px; font-size: 13px; color: #606266; }
.bar-row .val { width: 36px; text-align: right; font-size: 13px; color: #303133; }
</style>