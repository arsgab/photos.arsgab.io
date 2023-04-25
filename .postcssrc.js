const MANIFEST = 'dist/static/manifest.json';

module.exports = ({env}) => ({
  plugins: {
    'postcss-import': {},
    'postcss-nesting': {},
    'postcss-custom-media': {},
    'autoprefixer': {},
    'cssnano': env === 'production' ? {} : false,
    'postcss-hash': env === 'production' ? {manifest: MANIFEST} : false,
  }
});
