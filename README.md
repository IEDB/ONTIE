
# Ontology for Immune Epitopes
The Ontology of Immune Epitopes (ONTIE) is an effort to represent terms in the immunology domain in a formal ontology with the specific goal of representing experiments that identify and characterize immune epitopes. ONTIE is (at this development stage) a virtual ontology, drawing together terms from multiple reference ontologies.

This is the developer repository for ONTIE. You can learn more about ONTIE through our [documentation](https://ontology.iedb.org/resources/ONTIE).

# Editing

Our ontology terms come in three groups. Depending on what type of term you want to edit or add, you have to go through different routes:

1. template terms: We use [ROBOT templates](http://robot.obolibrary.org/template) to convert spreadsheets to OWL. Edit the relevant [`src/ontology/templates/`](src/ontology/templates/) file:
    - [`assays.tsv`](src/ontology/templates/assays.tsv) for assays related to immune epitopes
    - [`complex.tsv`](src/ontology/templates/complex.tsv) for protein complexes
    - [`disease.tsv`](src/ontology/disease.tsv) for diseases
    - [`external.tsv`](src/ontology/external.tsv) external terms from 
Chemical Entities of Biological Interest (CHEBI), NCBI Taxon, Gene Ontology (GO), NCBI Taxon database, and other sources
    - [`index.tsv`](src/ontology/index.tsv) list of ONTIE terms 
    - [`other.tsv`](src/ontology/other.tsv) all miscellaneous ontology terms 
    - [`predicate.tsv`](src/ontology/predicate.tsv) top level terms 
    - [`protein.tsv`](src/ontology/protein.tsv) all protein related terms in ONTIE
    - [`taxon.tsv`](src/ontology/taxon.tsv) NCBI Taxon, biological tax
    

See below for a full list of files, build instructions, and instructions on using Git and GitHub for ONTIE.


# Files

- [`README.md`](README.md) this overview document
- [`ontie.owl`](ontie.owl) the latest release of ONTIE
- [`Makefile`](Makefile) scripts for building ONTIE
- [`src/`](src/)
    - [`ontology/`](src/ontology/) source files for ONTIE
    - [`obsolete/`](src/obsolete) Contains obsolete code files
    - [`scripts`](src/scripts) utility scripts


# Building

The [`Makefile`](Makefile) contains scripts for building ONTIE. On macOS or Linux, you should just be able to run `make` or one of the specific tasks below. On Windows consider using some sort of Linux virtual machine such as Docker or Vagrant. Most results will be in the `build/` directory. If you have trouble, contact [James](mailto:james@overton.ca).

- `make test` merge and run SPARQL tests (this is run on every push to GitHub)
- `make sort` sort templates, and fix quoting and line endings, see more in [Keeping Things Tidy](#keeping-things-tidy) section
- `make modules` update ROBOT templates
- `make ONTIE.owl` build the release file; reasoning can take about 10 minutes
- `make views` update ROBOT templates
- `make all` prepare for a release, runs `imports`, `modules`, `test`, `ONTIE.owl`, and `views`
- `make build/ONTIE_merged.owl` merge `ONTIE-edit.owl` into a single file, don't reason
- `make clean` remove temporary files


# Development

We use git and GitHub to develop ONTIE. There's a lot of good documentation on both:

- git [website](https://git-scm.com) with files and documentation
- GitHub [Help](https://help.github.com) and [Flow](https://guides.github.com/introduction/flow/)
- [git command-line overview](http://dont-be-afraid-to-commit.readthedocs.io/en/latest/git/commandlinegit.html)


## Initial Set Up

Before you can start developing with ONTIE, you will need to do some initial setup:

1. Sign up for a [GitHub account](https://github.com)
2. Install the [Git command line tool](https://help.github.com/articles/set-up-git/), the [GitHub Desktop app](https://help.github.com/articles/set-up-git/), or another Git client of your choosing
3. [Configure Git with your name and email](https://help.github.com/articles/setting-your-username-in-git/)
4. [Clone the ONTIE repository](https://help.github.com/articles/cloning-a-repository/)
5. If you're using macOS and Excel, set up a pre-commit hook (see below for details):

       `ln -s ../../src/scripts/check-line-endings.sh .git/hooks/pre-commit`


## Making Changes

Changes should be made in manageable pieces, e.g. add one term or edit a few related terms. Most changes should correspond to a single issue on the tracker.

Start from a local copy of the `master` branch of the ONTIE repository. Make sure your local copy is up-to-date. Make your changes on a new branch. Please use the [TODO: ?] sheet to manage new IDs.

When you're ready, push your branch to the ONTIE repository and make a Pull Request (PR) on the GitHub website. Your PR is a request to merge your branch back into `master`. Your PR will be tested, discussed, adjusted if necessary, then merged. Then the cycle can repeat for the next change that you or another developer will make.

These are the steps with their CLI commands. When using a GUI application the steps will be the same.

1. `git fetch` make sure your local copy is up-to-date
2. `git checkout master` start on the `master` branch
3. `git checkout -b your-branch-name` create a new branch named for the change you're making
4. make your changes
5. `git status` and `git diff` inspect your changes
6. `git add --update src/` add all updated files in the `src/` directory to staging
7. `git commit --message "Description, issue #123"` commit staged changes with a message; it's good to include an issue number
8. `git push --set-upstream origin your-branch-name` push your commit to GitHub
9. open <https://github.com/IEDB/ONTIE> in your browser and click the "Make Pull Request" button. Enter the details of the changes you intend to contribute.

Your Pull Request will be automatically tested. If there are problems, we will update your branch. When all tests have passed, your PR can be merged into `master`. Rinse and repeat!


## Keeping Things Tidy

The easiest way to edit our `src/ontology/template/` files is with Excel. Unfortunately Excel on macOS [uses old line endings](http://developmentality.wordpress.com/2010/12/06/excel-2008-for-macs-csv-bug/), and this messes up our diffs.

For clean diffs, we also like to keep out templates sorted by ID.

The `make sort` command will fix line endings and sorting by running all the templates through a Python script.

