import sys
import os

extensions = ['sphinx.ext.mathjax','sphinx.ext.autosummary',
              'sphinx.ext.autodoc', 'sphinxcontrib.lunrsearch',
              'sphinxcontrib.autodoc_doxygen']

autosummary_generate = True
autodoc_member_order = 'bysource'

source_suffix = '.rst'
master_doc = 'index'

project = u'OpenMM'
copyright = u'2015, Stanford University and the Authors'

version = '@OPENMM_VERSION_MAJOR@.@OPENMM_VERSION_MINOR@'
release = '@OPENMM_VERSION_MAJOR@.@OPENMM_VERSION_MINOR@.@OPENMM_VERSION_TWEAK@'

exclude_patterns = ['_build', '_templates']
html_static_path = ['_static']
templates_path = ['_templates']

pygments_style = 'sphinx'

html_theme = "alabaster"
html_theme_options = {
    'description': "High performance molecular simulation on GPUs",
    'github_button': False,
    # 'github_user': 'pandegroup',
    # 'github_repo': 'openmm',
    'logo_name': False,
    'logo': 'logo.png',
}
html_sidebars = {
    '**': [
        'about.html',
        'searchbox.html',
        'navigation.html',
    ]
}

doxygen_xml = "doxygen/xml"
