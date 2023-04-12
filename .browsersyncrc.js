module.exports = {
  proxy: 'localhost:8000',
  files: ['dist/static/*.css', 'dist/*.html'],
  watchEvents: ['change', 'add', 'unlink'],
  open: 'local',
  reloadOnRestart: true,
  notify: false,
  scrollProportionally: false,
  scrollThrottle: 100,
  minify: false,
}
