// -----------------------------------------------------------
var gulp 			= require('gulp'),
	//sass 			= require('gulp-sass'),
	sass = require('gulp-sass')(require('sass')),
	autoPrefixer 	= require('gulp-autoprefixer'),
	minifyCSS 		= require('gulp-minify-css'),
	browserify 		= require('gulp-browserify'),
	uglify 			= require('gulp-uglify'),
	concat			= require('gulp-concat'),
	copy 			= require('gulp-copy'),
	livereload 		= require('gulp-livereload'),
	jade 			= require('gulp-jade'),
	imagemin 		= require('gulp-imagemin'),
	cache 			= require('gulp-cache'),
	webserver 		= require('gulp-webserver'),
	iconfont 		= require('gulp-iconfont'),
	iconfontCss 	= require('gulp-iconfont-css');
// -----------------------------------------------------------


gulp.task('sass', function() {
	return gulp.src("src/sass/*.scss")
	.pipe(sass())
	.on('error', function(error) {
		console.log(error);
		this.emit('end');
	})
	.pipe(autoPrefixer())
	.pipe(minifyCSS())
	.pipe(gulp.dest("build/css"));
});
gulp.task('templates', function() {
  return gulp.src('src/jade/**/*.jade')
	.pipe(jade({}))
	.on('error', function(error) {
		console.log(error);
		this.emit('end');
	})
	.pipe(gulp.dest('./build'))
});
gulp.task('images', function() {
  return gulp.src('./src/images/**/*')
    .pipe(cache(
    	imagemin(
    		{
    			optimizationLevel: 3,
    			progressive: true,
    			interlaced: true
    		}
    	)
    ))
    .pipe(gulp.dest('./build/img'));
});
gulp.task('browserify', function() {
	return gulp.src(['src/javascripts/main.js'])
	.pipe(browserify({
		insertGlobals: true,
		debug: true
	}))
	.on('error', function(error) {
		console.log(error);
		this.emit('end');
	})
	.pipe(uglify())
	.pipe(concat('app.js'))
	.pipe(gulp.dest('build/js'));
});

gulp.task('bundle-libs', function() {
  return gulp.src('src/javascripts/o3djs/*.js')
    .pipe(concat('bundle.js'))
    // .pipe(uglify())
    .pipe(gulp.dest('build/js'));
});

gulp.task('insert-bin',function(){
	return gulp.src('src/bin/**')
	.pipe(copy('build/bin',{
		prefix:2
	}));
});

gulp.task('iconfont', function(){
	return gulp.src(['src/icons/*.svg'])
	.pipe(iconfontCss({
		fontName: "icons",
		path: 'src/assets/templates/_icons.scss',
		targetPath: '../../../../src/sass/fonts/_icons.scss',
		fontPath: '../bin/fonts/icons/'
	}))
	.pipe(iconfont({
		fontName: "icons",
		normalize: true
	}))
	.pipe(gulp.dest('build/bin/fonts/icons/'));
});

gulp.task('webserver', function() {
  return gulp.src('./build')
    .pipe(webserver({
      livereload: true,
      open: true,
      fallback: 'index.html'
    }));
});
gulp.task('watch', function() {
	gulp.watch("src/icons/**/*.svg", 		gulp.series('iconfont'		));
	gulp.watch("src/assets/**/*", 			gulp.series('iconfont'		));
	gulp.watch("src/sass/**/*", 			gulp.series('sass'			));
	gulp.watch('src/jade/**/*.jade', 		gulp.series('templates'	));
	gulp.watch('src/javascripts/**', 		gulp.series('browserify'	));
	gulp.watch('src/javascripts/lib/**', 	gulp.series('bundle-libs'	));
	gulp.watch('src/images/**', 			gulp.series('images'		));
	gulp.watch('src/bin/**', 				gulp.series('insert-bin'	));
});
gulp.task('build-all',gulp.series('iconfont','sass','templates','browserify','bundle-libs','images','insert-bin'));
gulp.task('default',gulp.series('watch','webserver'));
