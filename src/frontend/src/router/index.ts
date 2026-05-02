import { createRouter, createWebHistory } from 'vue-router'

import MainLayout from '../layouts/MainLayout.vue'
import { pinia } from '../store'
import { useAuthStore } from '../store/auth'
import AuthView from '../views/auth/AuthView.vue'
import DiscoverView from '../views/discover/DiscoverView.vue'
import DiscoverViewUpstream from '../views/discover/DiscoverViewUpstream.vue'
import GraphView from '../views/graph/GraphView.vue'
import LibraryView from '../views/library/LibraryView.vue'
import PaperPDFView from '../views/library/paper/PaperPDFView.vue'
import NotFoundView from '../views/NotFoundView.vue'
import PaperList from '../views/library/PaperList.vue'
const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      redirect: '/app/library',
    },
    {
      path: '/login',
      name: 'login',
      component: AuthView,
      meta: {
        title: 'Scider | 登录',
        guestOnly: true,
      },
    },
    {
      path: '/app',
      component: MainLayout,
      meta: {
        requiresAuth: true,
      },
      children: [
        {
          path: '',
          redirect: '/app/library',
        },
        {
          path: 'library',
          name: 'library',
          component: LibraryView,
          meta: {
            title: 'Scider | 文献库',
          },  
          children: [
            { path: '', redirect: { name: 'library-folder', params: { folderId: 'all' } } },
            { path: 'folder/:folderId', name: 'library-folder', component: PaperList },
          ]
        },
        {
          path: 'library/paper/:paperId/pdf',
          name: 'paper-pdf',
          component: PaperPDFView,
          meta: {
            title: 'Scider | PDF 预览',
          },
        },
        {
          path: 'graph',
          name: 'graph',
          component: GraphView,
          meta: {
            title: 'Scider | 知识图谱',
          },
        },
        {
          path: 'discover',
          name: 'discover',
          component: DiscoverView,
          meta: {
            title: 'Scider | 发现',
          },
        },
        {
          path: 'discover-upstream',
          name: 'discover-upstream',
          component: DiscoverViewUpstream,
          meta: {
            title: 'Scider | 上下游',
          },
        },
      ],
    },
    {
      path: '/:pathMatch(.*)*',
      name: 'not-found',
      component: NotFoundView,
      meta: {
        title: 'Scider | 页面未找到',
      },
    },
  ],
  scrollBehavior() {
    return { top: 0 }
  },
})

router.beforeEach((to) => {
  const authStore = useAuthStore(pinia)
  authStore.hydrate()

  if (typeof to.meta.title === 'string') {
    document.title = to.meta.title
  }

  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    return {
      path: '/login',
      query: {
        redirect: to.fullPath,
      },
    }
  }

  if (to.meta.guestOnly && authStore.isAuthenticated) {
    return '/app/library'
  }

  return true
})

export default router