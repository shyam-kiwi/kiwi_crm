import ContactsIcon from '@/components/Icons/ContactsIcon.vue'
import LeadsIcon from '@/components/Icons/LeadsIcon.vue'
import NoteIcon from '@/components/Icons/NoteIcon.vue'
import OrganizationsIcon from '@/components/Icons/OrganizationsIcon.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import TaskIcon from '@/components/Icons/TaskIcon.vue'
import TicketsIcon from '@/components/Icons/TicketsIcon.vue'
import LucideLayoutDashboard from '~icons/lucide/layout-dashboard'
import router from '@/router'

export const navigationItems = [
  {
    label: 'Dashboard',
    icon: LucideLayoutDashboard,
    route: 'Dashboard',
    desktopOnly: true,
  },
  // Kiwi: Contacts first, Deals hidden, Tickets added and Tasks moved up.
  { label: 'Contacts', icon: ContactsIcon, route: 'Contacts' },
  { label: 'Leads', icon: LeadsIcon, route: 'Leads' },
  // { label: 'Deals', icon: DealsIcon, route: 'Deals' },
  { label: 'Tickets', icon: TicketsIcon, route: 'Tickets' },
  { label: 'Tasks', icon: TaskIcon, route: 'Tasks' },
  { label: 'Organizations', icon: OrganizationsIcon, route: 'Organizations' },
  { label: 'Notes', icon: NoteIcon, route: 'Notes' },
  { label: 'Call Logs', icon: PhoneIcon, route: 'Call Logs' },
]

export function getNavigationItems({ mobile = false } = {}) {
  return navigationItems.filter(
    (item) => router.hasRoute(item.route) && (!mobile || !item.desktopOnly),
  )
}
