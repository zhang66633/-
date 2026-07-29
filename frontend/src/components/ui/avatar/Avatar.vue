<script setup lang="ts">
import type { PrimitiveProps } from 'reka-ui'
import { Primitive, useForwardProps } from 'reka-ui'
import { cn } from '@/lib/utils'

interface AvatarProps extends PrimitiveProps {
  class?: string
}

const props = withDefaults(defineProps<AvatarProps>(), {
  as: 'span',
})

const forwarded = useForwardProps(props)
</script>

<template>
  <Primitive
    v-bind="forwarded"
    :class="
      cn(
        'relative flex h-10 w-10 shrink-0 overflow-hidden rounded-sm',
        props.class,
      )
    "
  >
    <slot />
  </Primitive>
</template>
