<template>
  <div>
    <!-- <v-checkbox
      :model-value="isActive"
      @update:model-value="$emit('update:is-active', $event)"
      :label="label"
      density="compact"
      hide-details
      color="primary"
    /> -->
    <v-range-slider
      :model-value="modelValue"
      @update:model-value="$emit('update:model-value', $event)"
      @end="$emit('end')"
      :class="{ 'grayed-out': !isActive }"
      :min="min"
      :max="max"
      color="primary"
      class="mb-1"
      step="1"
      track-size="1"
      thumb-size="15"
      hide-details
    />
    <v-row :class="{ 'grayed-out': !isActive }">
      <v-col>
        <v-text-field
          :model-value="modelValue[0]"
          @update:model-value="modelValue[0] = +$event"
          type="number"
          @blur="
            $emit('update:model-value', range);
            $emit('end');
          "
          @keyup.enter="
            $emit('update:model-value', range);
            $emit('end');
          "
          :min="min"
          :max="max"
          label="Start"
          variant="outlined"
          density="compact"
          focusable
        />
      </v-col>

      <v-col>
        <v-text-field
          :model-value="modelValue[1]"
          @update:model-value="modelValue[1] = +$event"
          type="number"
          @blur="
            $emit('update:model-value', range);
            $emit('end');
          "
          @keyup.enter="
            $emit('update:model-value', range);
            $emit('end');
          "
          :min="min"
          :max="max"
          label="End"
          variant="outlined"
          density="compact"
        />
      </v-col>
    </v-row>
  </div>
</template>

<script lang="ts">
import { Component, Vue, toNative, Prop } from "vue-facing-decorator";

@Component({
  name: "cd-range-input",
  components: {},
  emits: ["end", "update:model-value", "update:is-active"],
})
class CdRangeInput extends Vue {
  @Prop() modelValue!: [number, number];
  @Prop() isActive!: boolean;
  @Prop() label!: string;
  @Prop() min!: number;
  @Prop() max!: number;

  public get range() {
    // Check date range cross over
    if (this.modelValue[0] > this.modelValue[1]) {
      // swap values
      const temp = this.modelValue[0];
      this.modelValue[0] = this.modelValue[1];
      this.modelValue[1] = temp;
    }
    // Clip values
    return [
      Math.max(this.min, this.modelValue[0]),
      Math.min(this.max, this.modelValue[1]),
    ];
  }
}
export default toNative(CdRangeInput);
</script>

<style lang="scss" scoped>
.grayed-out {
  opacity: 0.55;
}
</style>
