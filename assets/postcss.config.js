module.exports = {
  plugins: [
    require('awsm.css')({theme: 'black'}),
    require('autoprefixer'),
    require('cssnano'),
    require('postcss-hash')({manifest: 'dist/static/manifest.json'}),
  ]
};
