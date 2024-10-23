## Milton Keynes Chess Website Repository

This is the source repository for the [Milton Keynes Chess Club website](https://www.miltonkeyneschessclub.co.uk).

### Overview

The website is built using the [Jekyll static site generator](https://jekyllrb.com/) framework and built on the [minimal-mistakes](https://mmistakes.github.io/minimal-mistakes/) theme.

The site is hosted using [Github Pages](https://pages.github.com/) and this is configured in the settings of the [Github repo]((https://github.com/MiltonKeynesChessClub/clubwebsite). Anytime code is pushed to the `main` branch, then a pipeline is triggered to build the static pages and publish changes to the website.

### Getting the website running locally

1. Install `ruby`, `ruby-dev` and `ruby-gems` if not already installed (test with `gem --version` on your command line)
2. [Install jekyll](https://jekyllrb.com/docs/): `gem install bundler jekyll`
3. Clone this repo to a local directory
4. From the root of your new directory, execute the following in the commandline `bundle install`
5. Finally, to run the site, execute the following in the commandline: `bundle exec jekyll serve`

The site should be running at http://localhost:4000.

### Further documentation needed

TODO: as the structure of the site solidifies, provide guides for contributing content + other maintenance.