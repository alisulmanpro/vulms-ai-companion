export default defineContentScript({
  matches: ['https://*.vu.edu.pk/*'],
  main() {
    console.log('Hello content.');
  },
});
