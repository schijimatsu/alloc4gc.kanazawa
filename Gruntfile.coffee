PACKAGE_ROOT = '.'

proxySnippet = require('grunt-connect-proxy/lib/utils').proxyRequest

module.exports = (grunt) ->
  pkg = grunt.file.readJSON 'package.json'
  grunt.initConfig
    coffee:
      glob_to_multiple: 
        expand: true,
        flatten: false,
        cwd: "grunt/src",
        src: ['**/*.coffee'],
        dest: "grunt/dist",
        ext: '.js', 
        join: true, 

    sass:
      dist:
        files: [{
          expand: true, 
          flatten: false, 
          cwd: "grunt/src", 
          src: ['**/*.sass'],
          dest: "grunt/dist",
          ext: '.css'
        }]

    hogan:
      publish:
        options:
          namespace: "Templates" 
          prettify: true 
          defaultName: (filename) ->
            return filename.split('/').slice(-1)[0].split(".")[0]
        files:
          "grunt/dist/js/template.js": ["grunt/src/**/*.mustache"]

    copy:
      html:
        files: [{
          expand: true, 
          flatten: false, 
          cwd: 'grunt/src', 
          src: ['**/*.html'], 
          dest: 'grunt/dist', 
        }],
      dist:
        files: [{
          expand: true, 
          flatten: false, 
          cwd: 'grunt/dist', 
          src: ['**/*.css', '**/*.js', '**/*.png', '**/*.jpg', '**/*.gif', '**/*.html'], 
          dest: "#{PACKAGE_ROOT}", 
        }],

    connect:
      livereload:
        options:
          port: 9000,
          hostname: 'localhost',
          # keepalive: true, 
          livereload: true, 
          # open: false, 
          # middleware: (connect, options) ->
          #   return [proxySnippet]
          # ,

      # server:
      #   proxies: [{
      #     context: '/',
      #     host: 'localhost',
      #     port: 6543,
      #     https: false,
      #     changeOrigin: false,
      #   }]

    watch:
      options:
        livereload: true
      files: [
        "grunt/src/**/*.coffee", 
        "grunt/src/**/*.sass", 
        "grunt/src/**/*.mustache", 
        "grunt/src/**/*.html", 
      ]
      tasks: [
        'coffee',
        'sass',
        'hogan',
        'copy',
      ]
  
  for taskName of pkg.devDependencies when taskName.substring(0, 6) is 'grunt-'
    grunt.loadNpmTasks taskName

  grunt.registerTask 'build', [
    'coffee', 
    'sass', 
    'hogan', 
  ]

  grunt.registerTask 'dist', [
    'build', 
    'copy', 
  ]

  grunt.registerTask 'auto', [
    'dist', 
    'watch', 
  ]

  grunt.registerTask 'default', [
    'auto', 
  ]

  grunt.registerTask 'live', [
    'dist', 
    # 'configureProxies:server', 
    'connect:livereload', 
    'watch'
  ]
