import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Login',
    component: () => import('../components/Login.vue')
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('../components/Register.vue')
  },
  {
    path: '/chat',
    name: 'Chat',
    component: () => import('../components/Chat.vue'),
    meta: { requiresAuth: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const isLoggedIn = localStorage.getItem('user') !== null
  
  if (to.meta.requiresAuth && !isLoggedIn) {
    next('/')
  } else if ((to.path === '/' || to.path === '/register') && isLoggedIn) {
    next('/chat')
  } else {
    next()
  }
})

export default router
