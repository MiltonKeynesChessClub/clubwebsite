@echo off
rem Start the Jekyll server with the correct gem environment
call bundle exec jekyll serve --watch
rem Open the website in the default browser
start http://localhost:4000
rem Pause the command prompt to see the output
pause