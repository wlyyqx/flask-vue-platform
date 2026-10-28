<template>
  <el-container style="height: 100vh">
    <el-header class="header">
      <div class="logo">测试资源管理平台</div>
      <div class="user">
        <span>{{ userStore.user?.real_name || userStore.user?.username }}</span>
        <el-button link style="color:#fff" @click="logout">退出</el-button>
      </div>
    </el-header>
    <el-container>
      <el-aside width="220px" style="background:#f5f7fa; padding-top: 8px">
        <el-menu :default-active="$route.path" router>
          <el-menu-item index="/projects">📁 项目管理</el-menu-item>
          <template v-if="currentProjectId">
            <el-menu-item :index="`/projects/${currentProjectId}/cases`">📝 用例管理</el-menu-item>
            <el-menu-item :index="`/projects/${currentProjectId}/reviews`">👀 评审管理</el-menu-item>
            <el-menu-item :index="`/projects/${currentProjectId}/defects`">🐞 缺陷管理</el-menu-item>
            <el-menu-item :index="`/projects/${currentProjectId}/report`">📊 报表统计</el-menu-item>
          </template>
        </el-menu>
      </el-aside>
      <el-main>
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()
const route = useRoute()
const router = useRouter()

const currentProjectId = computed(() => route.params.id || null)

function logout() {
  userStore.logout()
  router.push('/login')
}
</script>

<style scoped>
.header {
  display: flex; justify-content: space-between; align-items: center;
  background: #409EFF; color: #fff;
}
.logo { font-size: 18px; font-weight: bold; }
.user { display: flex; gap: 12px; align-items: center; }
</style>