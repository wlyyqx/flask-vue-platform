import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/login', component: () => import('@/views/Login.vue'), meta: { public: true } },
  {
    path: '/',
    component: () => import('@/layouts/MainLayout.vue'),
    redirect: '/projects',
    children: [
      { path: 'projects', component: () => import('@/views/ProjectList.vue') },
      { path: 'projects/:id/cases', component: () => import('@/views/CaseList.vue') },
      { path: 'projects/:id/reviews', component: () => import('@/views/ReviewList.vue') },
      { path: 'projects/:id/defects', component: () => import('@/views/DefectList.vue') },
      { path: 'projects/:id/report', component: () => import('@/views/Report.vue') }
    ]
  }
]

const router = createRouter({ history: createWebHistory(), routes })

router.beforeEach((to, _from, next) => {
  const token = localStorage.getItem('access_token')
  if (to.meta.public) return next()
  if (!token) return next('/login')
  next()
})

export default router