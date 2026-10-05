<template>
  <LayoutHeader>
    <template #left-header>
      <Breadcrumbs :items="breadcrumbs">
        <template #prefix="{ item }">
          <Icon v-if="item.icon" :icon="item.icon" class="mr-2 h-4" />
        </template>
      </Breadcrumbs>
    </template>
    <template v-if="!errorTitle" #right-header>
      <CustomActions
        v-if="document._actions?.length"
        :actions="document._actions"
      />
      <CustomActions
        v-if="document.actions?.length"
        :actions="document.actions"
      />
      <AssignTo v-model="assignees.data" doctype="HD Ticket" :docname="ticketId" />
      <Dropdown
        v-if="doc && document.statuses"
        :options="statuses"
        placement="right"
      >
        <template #default="{ open }">
          <Button
            v-if="doc.status"
            :label="doc.status"
            :iconRight="open ? 'chevron-up' : 'chevron-down'"
          >
            <template #prefix>
              <IndicatorIcon :class="getTicketStatus(doc.status).color" />
            </template>
          </Button>
        </template>
      </Dropdown>
    </template>
  </LayoutHeader>
  <div v-if="doc.name" class="flex h-full overflow-hidden">
    <Tabs
      v-model="tabIndex"
      :tabs="tabs"
      class="flex flex-1 overflow-hidden flex-col [&_[role='tab']]:px-0 [&_[role='tablist']]:px-5 [&_[role='tablist']]:gap-7.5 [&_[role='tabpanel']:not([hidden])]:flex [&_[role='tabpanel']:not([hidden])]:grow"
    >
      <template #tab-panel="{ tab }">
        <div v-if="tab.name === 'Call Logs'" class="flex flex-1 flex-col overflow-hidden">
          <div v-if="callLogs.data?.length" class="activity mt-4">
            <div v-for="(call, i) in callLogs.data" :key="call.name">
              <div class="activity grid grid-cols-[30px_minmax(auto,_1fr)] gap-4 px-3 sm:px-10">
                <div
                  class="z-0 relative flex justify-center before:absolute before:left-[50%] before:-z-[1] before:top-0 before:border-l before:border-outline-gray-modals"
                  :class="i != callLogs.data.length - 1 ? 'before:h-full' : 'before:h-4'"
                >
                  <div class="flex h-8 w-7 items-center justify-center bg-surface-white text-ink-gray-8">
                    <MissedCallIcon v-if="call.status == 'No Answer'" class="text-ink-red-4" />
                    <DeclinedCallIcon v-else-if="call.status == 'Busy'" />
                    <component :is="call.type == 'Incoming' ? InboundCallIcon : OutboundCallIcon" v-else />
                  </div>
                </div>
                <CallArea class="mb-4" :activity="call" />
              </div>
            </div>
          </div>
          <EmptyState v-else :icon="PhoneIcon" name="Call Logs" />
        </div>
        <Activities
          v-else
          ref="activities"
          v-model:reload="reload"
          v-model:tabIndex="tabIndex"
          doctype="HD Ticket"
          :docname="ticketId"
          :tabs="tabs"
          @beforeSave="beforeSave"
          @afterSave="reloadAssignees"
        />
      </template>
    </Tabs>
    <Resizer class="flex flex-col justify-between border-l" side="right">
      <div
        class="flex h-[45px] cursor-copy items-center border-b px-5 py-2.5 text-lg font-medium text-ink-gray-9"
        @click="copyToClipboard(ticketId)"
      >
        {{ __(ticketId) }}
      </div>
      <div class="flex items-center justify-start gap-5 border-b p-5">
        <div class="flex flex-col gap-2.5 truncate">
          <Tooltip :text="doc.subject || __('Set Subject')">
            <div class="truncate text-2xl font-medium text-ink-gray-9">
              {{ title }}
            </div>
          </Tooltip>
          <div class="flex gap-1.5">
            <Button
              :tooltip="__('Send an Email')"
              :icon="Email2Icon"
              @click="
                doc.raised_by
                  ? openEmailBox()
                  : toast.error(
                      __('Please set a raised by email to send emails'),
                    )
              "
            />
            <Button
              v-if="callEnabled"
              :tooltip="__('Make a Call')"
              :icon="PhoneIcon"
              @click="
                doc.custom_phone_number
                  ? makeTicketCall(doc.custom_phone_number)
                  : toast.error(
                      __('Please set a phone number to make calls'),
                    )
              "
            />
            <Button
              :tooltip="__('Attach a File')"
              :icon="AttachmentIcon"
              @click="showFilesUploader = true"
            />
            <Button
              v-if="canDelete"
              :tooltip="__('Delete')"
              variant="subtle"
              theme="red"
              icon="trash-2"
              @click="deleteTicket"
            />
          </div>
          <ErrorMessage :message="__(error)" />
        </div>
      </div>
      <HDTicketSLASection
        v-if="doc.agreement_status"
        v-model="doc"
      />
      <div
        v-if="sections.data"
        class="flex flex-1 flex-col justify-between overflow-hidden"
      >
        <SidePanelLayout
          :sections="sections.data"
          doctype="HD Ticket"
          :docname="ticketId"
          @reload="sections.reload"
          @afterFieldChange="reloadAssignees"
        />
      </div>
    </Resizer>
  </div>
  <ErrorPage
    v-else-if="errorTitle"
    :errorTitle="errorTitle"
    :errorMessage="errorMessage"
  />
  <FilesUploader
    v-model="showFilesUploader"
    doctype="HD Ticket"
    :docname="ticketId"
    @after="
      () => {
        activities?.all_activities?.reload()
        changeTabTo('attachments')
      }
    "
  />
  <DeleteLinkedDocModal
    v-if="showDeleteLinkedDocModal"
    v-model="showDeleteLinkedDocModal"
    :doctype="'HD Ticket'"
    :docname="ticketId"
    name="Tickets"
  />
</template>

<script setup>
import DeleteLinkedDocModal from '@/components/DeleteLinkedDocModal.vue'
import ErrorPage from '@/components/ErrorPage.vue'
import Icon from '@/components/Icon.vue'
import Resizer from '@/components/Resizer.vue'
import ActivityIcon from '@/components/Icons/ActivityIcon.vue'
import EmailIcon from '@/components/Icons/EmailIcon.vue'
import Email2Icon from '@/components/Icons/Email2Icon.vue'
import CommentIcon from '@/components/Icons/CommentIcon.vue'
import DetailsIcon from '@/components/Icons/DetailsIcon.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import WhatsAppIcon from '@/components/Icons/WhatsAppIcon.vue'
import IndicatorIcon from '@/components/Icons/IndicatorIcon.vue'
import AttachmentIcon from '@/components/Icons/AttachmentIcon.vue'
import CallArea from '@/components/Activities/CallArea.vue'
import MissedCallIcon from '@/components/Icons/MissedCallIcon.vue'
import DeclinedCallIcon from '@/components/Icons/DeclinedCallIcon.vue'
import InboundCallIcon from '@/components/Icons/InboundCallIcon.vue'
import OutboundCallIcon from '@/components/Icons/OutboundCallIcon.vue'
import EmptyState from '@/components/ListViews/EmptyState.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import Activities from '@/components/Activities/Activities.vue'
import AssignTo from '@/components/AssignTo.vue'
import FilesUploader from '@/components/FilesUploader/FilesUploader.vue'
import SidePanelLayout from '@/components/SidePanelLayout.vue'
import HDTicketSLASection from '@/components/HDTicketSLASection.vue'
import CustomActions from '@/components/CustomActions.vue'
import {
  setupCustomizations,
  copyToClipboard,
} from '@/utils'
import { getView } from '@/utils/view'
import { getSettings } from '@/stores/settings'
import { globalStore } from '@/stores/global'
import { ticketStatusesStore } from '@/stores/ticketStatuses'
import { getMeta } from '@/stores/meta'
import { useDocument } from '@/data/document'
import { whatsappEnabled } from '@/composables/whatsapp'
import { callEnabled } from '@/composables/telephony'
import {
  createResource,
  Dropdown,
  Tooltip,
  Tabs,
  Breadcrumbs,
  call,
  usePageMeta,
  toast,
} from 'frappe-ui'
import { ref, computed, watch, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useActiveTabManager } from '@/composables/useActiveTabManager'

const { brand } = getSettings()
const { $dialog, $socket } = globalStore()
const { statusOptions, getTicketStatus } = ticketStatusesStore()
const { doctypeMeta } = getMeta('HD Ticket')

const route = useRoute()
const router = useRouter()

const props = defineProps({
  ticketId: { type: String, required: true },
})

const reload = ref(false)
const activities = ref(null)
const errorTitle = ref('')
const errorMessage = ref('')
const showDeleteLinkedDocModal = ref(false)
const showFilesUploader = ref(false)

const { triggerOnChange, assignees, permissions, document, scripts, error } =
  useDocument('HD Ticket', props.ticketId)

const canDelete = computed(() => permissions.data?.permissions?.delete || false)

const doc = computed(() => document.doc || {})

watch(error, (err) => {
  if (err) {
    errorTitle.value = __(
      err.exc_type == 'DoesNotExistError'
        ? 'Document not found'
        : 'Error occurred',
    )
    errorMessage.value = __(err.messages?.[0] || 'An error occurred')
  } else {
    errorTitle.value = ''
    errorMessage.value = ''
  }
})

// KIWI: recompute form-script actions when the fields that gate them change
// (category decides eligibility; bb_share_status flips the Share button to the
// "Shared" chip), not just once at load. Keyed on those fields so it does not
// re-run on every keystroke. Re-apply after a crm upgrade — see the Resolution
// column patch. Upstream used `{ once: true }` watching `document.doc`.
watch(
  () => {
    const d = document.doc || {}
    return [d.name, d.category, d.bb_share_status].join('')
  },
  async () => {
    const _doc = document.doc
    if (!_doc || !scripts.data?.length) return
    let s = await setupCustomizations(scripts.data, {
      doc: _doc,
      $dialog,
      $socket,
      router,
      toast,
      updateField,
      createToast: toast.create,
      deleteDoc: deleteTicket,
      call,
    })
    document._actions = s.actions || []
    document._statuses = s.statuses || []
  },
  { immediate: true },
)

const breadcrumbs = computed(() => {
  let items = [{ label: __('Tickets'), route: { name: 'Tickets' } }]

  if (route.query.view || route.query.viewType) {
    let view = getView(route.query.view, route.query.viewType, 'HD Ticket')
    if (view) {
      items.push({
        label: __(view.label),
        icon: view.icon,
        route: {
          name: 'Tickets',
          params: { viewType: route.query.viewType },
          query: { view: route.query.view },
        },
      })
    }
  }

  items.push({
    label: title.value,
    route: { name: 'Ticket', params: { ticketId: props.ticketId } },
  })
  return items
})

const title = computed(() => {
  let t = doctypeMeta.value?.title_field || 'name'
  return doc.value?.[t] || props.ticketId
})

const statuses = computed(() => {
  let customStatuses = document.statuses?.length
    ? document.statuses
    : document._statuses || []
  return statusOptions(customStatuses, triggerStatusChange)
})

usePageMeta(() => {
  return { title: title.value, icon: brand.favicon }
})

const tabs = computed(() => {
  let tabOptions = [
    {
      name: 'Data',
      label: __('Ticket Details'),
      icon: DetailsIcon,
    },
    {
      name: 'Activity',
      label: __('Activity'),
      icon: ActivityIcon,
    },
    {
      name: 'Emails',
      label: __('Emails'),
      icon: EmailIcon,
    },
    {
      name: 'Comments',
      label: __('Comments'),
      icon: CommentIcon,
    },
    {
      name: 'Call Logs',
      label: __('Call Logs'),
      icon: PhoneIcon,
      count: computed(() => callLogs.data?.length),
    },
    {
      name: 'Attachments',
      label: __('Attachments'),
      icon: AttachmentIcon,
    },
    {
      name: 'WhatsApp',
      label: __('WhatsApp'),
      icon: WhatsAppIcon,
      condition: () => whatsappEnabled.value,
    },
  ]
  return tabOptions.filter((tab) => (tab.condition ? tab.condition() : true))
})

const { tabIndex, changeTabTo } = useActiveTabManager(tabs, 'lastTicketTab')

const sections = createResource({
  url: 'crm.fcrm.doctype.crm_fields_layout.crm_fields_layout.get_sidepanel_sections',
  cache: ['sidePanelSections', 'HD Ticket'],
  params: { doctype: 'HD Ticket' },
  auto: true,
})

const callLogs = createResource({
  url: 'kiwi.api.ticket.get_linked_call_logs',
  cache: ['ticket_call_logs', props.ticketId],
  params: { ticket: props.ticketId },
  auto: true,
})

async function triggerStatusChange(value) {
  await triggerOnChange('status', value)
  document.save.submit()
}

function beforeSave() {
  document.save.submit()
}

function updateField(name, value) {
  value = Array.isArray(name) ? '' : value
  let oldValues = Array.isArray(name) ? {} : doc.value[name]

  if (Array.isArray(name)) {
    name.forEach((field) => (doc.value[field] = value))
  } else {
    doc.value[name] = value
  }

  document.save.submit(null, {
    onSuccess: () => (reload.value = true),
    onError: (err) => {
      if (Array.isArray(name)) {
        name.forEach((field) => (doc.value[field] = oldValues[field]))
      } else {
        doc.value[name] = oldValues
      }
      toast.error(err.messages?.[0] || __('Error updating field'))
    },
  })
}

function deleteTicket() {
  showDeleteLinkedDocModal.value = true
}

function openEmailBox() {
  let currentTab = tabs.value[tabIndex.value]
  if (!['Emails', 'Comments', 'Activities'].includes(currentTab.name)) {
    activities.value.changeTabTo('emails')
  }
  nextTick(() => (activities.value.emailBox.show = true))
}

function reloadAssignees(data) {
  if (Object.hasOwn(data ?? {}, 'ticket_owner')) {
    assignees.reload()
  }
}

const ticketCall = createResource({
  url: 'kiwi.api.ticket.make_call',
  makeParams: ({ to_number }) => ({
    ticket: props.ticketId,
    to_number,
  }),
  onSuccess(res) {
    const message = res?.data?.message || __('Call initiated')
    toast.success(message)
    setTimeout(() => callLogs.reload(), 1500)
  },
  onError(err) {
    toast.error(err.messages?.[0] || __('Failed to initiate call'))
  },
})

function makeTicketCall(number) {
  ticketCall.submit({ to_number: number })
}
</script>
