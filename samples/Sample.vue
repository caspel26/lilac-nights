<script setup lang="ts">
import { ref } from "vue";

const props = defineProps<{ title: string }>();
const count = ref(0);
const items = ref(["a", "b"]);

function increment() {
  count.value++;
}
</script>

<template>
  <section class="card" :class="{ active: count > 0 }">
    <h1>{{ props.title }}</h1>
    <button @click="increment">Clicked {{ count }} times</button>
    <ul>
      <li v-for="item in items" :key="item">{{ item }}</li>
    </ul>
    <p v-if="count > 3">Many clicks</p>
    <slot name="footer" />
    <template #header><span>Header</span></template>
  </section>
</template>

<style scoped>
.card {
  color: #d7b8ff;
}
</style>
