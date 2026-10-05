import { createResource } from 'frappe-ui'
import { computed, ref } from 'vue'

const integrations = ref({})
export const defaultCallingMedium = ref('')
export const callEnabled = ref(false)
// Kiwi: Ozonetel is served by the ozonetel_integration app, which overrides
// is_call_integration_enabled. `isOzonetelAgent` gates the Ozonetel toolbar.
export const isOzonetelAgent = ref(false)

createResource({
  url: 'crm.integrations.api.is_call_integration_enabled',
  cache: 'Is Call Integration Enabled',
  auto: true,
  onSuccess: (data) => {
    // Accept the legacy flat shape (`twilio_enabled`, `exotel_enabled`,
    // `ozonetel_enabled`) too, until ozonetel_integration's override returns
    // `integrations`.
    integrations.value = data.integrations || {
      twilio: Boolean(data.twilio_enabled),
      exotel: Boolean(data.exotel_enabled),
      ozonetel: Boolean(data.ozonetel_enabled),
    }
    isOzonetelAgent.value = Boolean(data.is_ozonetel_agent)
    defaultCallingMedium.value = data.default_calling_medium
    callEnabled.value = Object.values(integrations.value).some(Boolean)
  },
})

export function setEnabled(name, value) {
  integrations.value[name] = value
  callEnabled.value = Object.values(integrations.value).some(Boolean)
}

export function useTelephony() {
  const allIntegrations = computed(() =>
    Object.entries(integrations.value).map(([name, enabled]) => ({
      name,
      enabled,
    })),
  )

  function isEnabled(name) {
    return Boolean(integrations.value[name])
  }

  const isAnyEnabled = computed(() =>
    Object.values(integrations.value).some(Boolean),
  )

  return { integrations: allIntegrations, isEnabled, isAnyEnabled }
}
