const MANIFEST = 'dist/static/manifest.json';

module.exports = ({env}) => ({
  plugins: {
    'postcss-import': {},
    'postcss-nesting': {},
    'autoprefixer': {},
    'cssnano': env === 'production' ? {} : false,
    'postcss-hash': env === 'production' ? {manifest: MANIFEST} : false,
  }
});
