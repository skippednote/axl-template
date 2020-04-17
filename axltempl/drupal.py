import argparse
import json
import os
import pkgutil
import shutil


def main():
    args = get_arguments()

    if (os.path.isdir(args.directory)):
        if (not args.force):
            print(
                f'The "{args.directory}" directory already exists. Please delete it before running or use the -f option.')
            return 2
        print(f'Removing "{args.directory}" directory..."')
        shutil.rmtree(args.directory, True)

    os.mkdir(args.directory)
    os.chdir(args.directory)
    os.system('git init; git commit --allow-empty -m "Initial commit"')

    generateDrupalFiles(name=args.name, description=args.description,
                        core=args.core_package, docroot=args.docroot, cacheService=args.cache)

    if not args.no_install:
        os.system('composer install -o')

    os.chdir('..')
    return 0


def generateDrupalFiles(name, description='', core='core', docroot='web', cacheService=''):
    composer = getComposerTemplate(
        name=name, description=description, core=core, docroot=docroot, cacheService=cacheService)
    composer = sortComposerPackages(composer)
    with open('composer.json', 'w') as composer_file:
        json.dump(composer, composer_file, indent=4)
    with open('.gitignore', 'w') as gitignore_file:
        gitignore_file.write(getGitignore(docroot))

    with open('load.environment.php', 'w') as f:
        f.write(pkgutil.get_data(
            __name__, "files/drupal/load.environment.php").decode())
    with open('.env.example', 'w') as f:
        f.write(pkgutil.get_data(__name__, "files/drupal/.env.example").decode())

    os.mkdir('drush')
    os.mkdir('drush/sites')
    with open('drush/drush.yml', 'w') as f:
        f.write(pkgutil.get_data(__name__, "files/drupal/drush.yml").decode())
    with open('drush/sites/self.site.yml', 'w') as f:
        f.write(pkgutil.get_data(__name__, "files/drupal/self.site.yml").decode())

    pass


def getComposerTemplate(name, description, core, docroot, cacheService):
    composer = json.loads(pkgutil.get_data(
        __name__, "files/drupal/composer.json"))
    composer['name'] = name
    composer['description'] = description
    composer['extra']['drupal-scaffold']['locations']['web-root'] = docroot + '/'
    composer['extra']['installer-paths'] = {
        docroot + '/core': ['type:drupal-core'],
        docroot + '/libraries/{$name}': ['type:drupal-library'],
        docroot + '/modules/contrib/{$name}': ['type:drupal-module'],
        docroot + '/profiles/contrib/{$name}': ['type:drupal-profile'],
        docroot + '/themes/contrib/{$name}': ['type:drupal-theme'],
        'drush/Commands/contrib/{$name}': ['type:drupal-drush'],
        docroot + '/modules/custom/{$name}': ['type:drupal-custom-module'],
        docroot + '/themes/custom/{$name}': ['type:drupal-custom-theme']
    }

    if (core == 'core'):
        composer['require']['drupal/core'] = '^8.8'
    if (core == 'recommended'):
        composer['require']['drupal/core-recommended'] = '^8.8'
    if (cacheService == 'redis'):
        composer['require']['drupal/redis'] = '^1.2'
    if (cacheService == 'memcache'):
        composer['require']['drupal/redis'] = '^1.2'
    return composer


def sortComposerPackages(composer):
    composer['require'] = sortDictionaryByKeys(composer['require'])
    composer['require-dev'] = sortDictionaryByKeys(composer['require-dev'])
    return composer


def sortDictionaryByKeys(dict):
    sortedDict = {}
    for key in sorted(dict.keys()):
        sortedDict[key] = dict[key]
    return sortedDict


def getGitignore(docroot):
    gitignore = pkgutil.get_data(
        __name__, "files/drupal/.gitignore.template").decode()
    gitignore = gitignore.replace('{docroot}', docroot)
    return gitignore


def get_arguments():
    parser = argparse.ArgumentParser(
        description='Scaffold a Drupal site template')
    parser.add_argument('name', action='store',
                        help='Name of your application package (e.g., axelerant/site)')
    parser.add_argument('--directory', '-d', action='store', default='drupal',
                        help='Directory where the files should be set up (e.g., drupal). The directory will be emptied.')
    parser.add_argument('--description', '-D', action='store', default='',
                        help='Description of the package')
    parser.add_argument('--core-package', '-c', action='store', default='core',
                        choices=['core', 'recommended'], help='Select the core package')
    parser.add_argument('--docroot', '-r', action='store', default='web',
                        help='The document root')
    parser.add_argument('--force', '-f', action='store_true',
                        help='Force delete the "drupal" directory if it exists')
    parser.add_argument('--no-install', action='store_true',
                        help='Do not run composer install')
    parser.add_argument('--cache', action='store', default='',
                        help='Add a cache service (either redis or memcache)')
    return parser.parse_args()
