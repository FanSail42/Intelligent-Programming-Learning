import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import MainLayout from '@/layouts/MainLayout.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/LoginView.vue'),
      meta: { public: true },
    },
    {
      path: '/403',
      name: 'forbidden',
      component: () => import('@/views/ForbiddenView.vue'),
      meta: { public: true },
    },
    {
      path: '/',
      component: MainLayout,
      redirect: '/login',
      children: [
        {
          path: 'student/courses',
          name: 'student-courses',
          component: () => import('@/views/student/StudentCourseList.vue'),
          meta: { roles: ['student'] },
        },
        {
          path: 'student/browse',
          name: 'student-browse',
          component: () => import('@/views/student/StudentCourseBrowse.vue'),
          meta: { roles: ['student'] },
        },
        {
          path: 'student/chat',
          name: 'student-chat',
          component: () => import('@/views/student/StudentChat.vue'),
          meta: { roles: ['student'] },
        },
        {
          path: 'student/code',
          name: 'student-code',
          component: () => import('@/views/student/StudentCode.vue'),
          meta: { roles: ['student'] },
        },
        {
          path: 'student/code/history',
          name: 'student-code-history',
          component: () => import('@/views/student/StudentCodeHistory.vue'),
          meta: { roles: ['student'] },
        },
        {
          path: 'student/dashboard',
          name: 'student-dashboard',
          component: () => import('@/views/student/StudentDashboard.vue'),
          meta: { roles: ['student'] },
        },
        {
          path: 'student/wrong-book',
          name: 'student-wrong-book',
          component: () => import('@/views/student/StudentWrongBook.vue'),
          meta: { roles: ['student'] },
        },
        {
          path: 'teacher/courses',
          name: 'teacher-courses',
          component: () => import('@/views/teacher/TeacherCourseList.vue'),
          meta: { roles: ['teacher', 'admin'] },
        },
        {
          path: 'teacher/materials',
          name: 'teacher-materials',
          component: () => import('@/views/teacher/TeacherMaterials.vue'),
          meta: { roles: ['teacher', 'admin'] },
        },
        {
          path: 'teacher/warehouses',
          name: 'teacher-warehouses',
          component: () => import('@/views/warehouse/WarehouseList.vue'),
          meta: { roles: ['teacher', 'admin'] },
        },
        {
          path: 'teacher/warehouses/:id',
          name: 'teacher-warehouse-detail',
          component: () => import('@/views/warehouse/WarehouseDetail.vue'),
          meta: { roles: ['teacher', 'admin'] },
        },
      ],
    },
  ],
})

router.beforeEach(async (to, _from, next) => {
  const auth = useAuthStore()

  if (to.meta.public) {
    if (to.path === '/login' && auth.isLoggedIn) {
      return next(auth.role === 'student' ? '/student/courses' : '/teacher/courses')
    }
    return next()
  }

  if (!auth.isLoggedIn) {
    return next('/login')
  }

  if (!auth.user) {
    try {
      await auth.fetchMe()
    } catch {
      auth.clearAuth()
      return next('/login')
    }
  }

  const roles = to.meta.roles as string[] | undefined
  if (roles && auth.role && !roles.includes(auth.role)) {
    return next('/403')
  }

  return next()
})

export default router
