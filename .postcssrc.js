module.exports = ({env}) => ({
  plugins: {
    'postcss-import': {},
    'postcss-nesting': {},
    'postcss-custom-media': {},
    'autoprefixer': {},
    'cssnano': env === 'production' ? {} : false,
  }
});
