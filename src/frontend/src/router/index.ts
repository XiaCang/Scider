import { createRouter, createWebHistory } from 'vue-router'

import MainLayout from '../layouts/MainLayout.vue'
import { pinia } from '../store'
import { useAuthStore } from '../store/auth'
import AuthView from '../views/auth/AuthView.vue'
import DashboardView from '../views/dashboard/DashboardView.vue'
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
      redirect: '/app/dashboard',
    },
    {
      path: '/login',
      name: 'login',
      component: AuthView,
      meta: {
        title: 'Scider | Login',
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
          redirect: '/app/dashboard',
        },
        {
          path: 'dashboard',
          name: 'dashboard',
          component: DashboardView,
          meta: {
            title: 'Scider | Dashboard',
          },
        },
        {
          path: 'library',
          name: 'library',
          component: LibraryView,
          meta: {
            title: 'Scider | Library',
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
            title: 'Scider | PDF Preview',
          },
        },
        {
          path: 'graph',
          name: 'graph',
          component: GraphView,
          meta: {
            title: 'Scider | Knowledge Graph',
          },
        },
        {
          path: 'discover',
          name: 'discover',
          component: DiscoverView,
          meta: {
            title: 'Scider | Discover',
          },
        },
        {
          path: 'discover-upstream',
          name: 'discover-upstream',
          component: DiscoverViewUpstream,
          meta: {
            title: 'Scider | Discover Upstream',
          },
        },
      ],
    },
    {
      path: '/:pathMatch(.*)*',
      name: 'not-found',
      component: NotFoundView,
      meta: {
        title: 'Scider | Not Found',
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
    return '/app/dashboard'
  }

  return true
})

export default router