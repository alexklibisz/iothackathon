/**
 * Commands:
 * - gulp webserver - starts a webserver that listens for file changes and reloads the page
 * - gulp livewebserver - start a webserver with no live reload, but file changes are still recognized on manual reload
 */

var gulp = require('gulp'),
  gutil = require('gulp-util'),
  webserver = require('gulp-webserver');

gulp.task('js', function() {
  gulp.src('components/**/*.js')
});

gulp.task('html', function() {
  gulp.src('components/**/*.html')
});

gulp.task('css', function() {
  gulp.src('components/**/*.css')
});

gulp.task('watch', function() {
  gulp.watch('components/**/*.js', ['js']);
  gulp.watch('components/**/*.css', ['css']);
  gulp.watch(['components/**/*.html',
    'index.html'], ['html']);
});

gulp.task('webserver', function() {
  gulp.src('.')
    .pipe(webserver({
      livereload: true,
      open: true
    }));
});

gulp.task('livewebserver', function() {
  gulp.src('.')
    .pipe(webserver({
      livereload: false,
      open: true
    }));
});

gulp.task('dev', ['watch', 'html', 'js', 'css', 'webserver']);
gulp.task('live', ['livewebserver']);
