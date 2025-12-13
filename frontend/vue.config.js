const { defineConfig } = require('@vue/cli-service')

module.exports = defineConfig({
  transpileDependencies: true,
  
  chainWebpack: config => {
    config.plugin('html').tap(args => {
      args[0].ymapsApiKey = process.env.GEOCODER_API_KEY;
      return args;
    });
  }})