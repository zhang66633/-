<script setup lang="ts">
import type { PrimitiveProps } from 'reka-ui'
import { AccordionHeader, AccordionTrigger } from 'reka-ui'
import { ChevronDown } from 'lucide-vue-next'
import { cn } from '@/lib/utils'

interface Props extends PrimitiveProps {
  class?: string
}

const props = withDefaults(defineProps<Props>(), {
  as: 'button',
})
</script>

<template>
  <AccordionHeader class="flex">
    <AccordionTrigger as-child>
      <slot>
        <button
          :class="
            cn(
              'flex flex-1 items-center justify-between py-4 text-sm font-medium transition-all hover:underline',
              '[&[data-state=open]>svg]:rotate-180',
              props.class,
            )
          "
        >
          <slot name="title" />
          <ChevronDown class="h-4 w-4 shrink-0 transition-transform duration-200" />
        </button>
      </slot>
    </AccordionTrigger>
  </AccordionHeader>
</template>
