Guidelines for contributing
===========================

Here are some guidelines for contributing new features, fixing bugs and overall
adding new code to this project.

Thank you for contributing Melex-Rodao! We want to make contributing to this project as easy and transparent as possible, whether it's:

- Reporting a bug
- Discussing the current state of the code
- Submitting a fix
- Proposing new features
- Becoming a maintainer


Workflow    
----------------------
We all work with a [Fork](https://www.atlassian.com/git/tutorials/comparing-workflows/forking-workflow) + [Github workflow](https://guides.github.com/introduction/flow/index.html).  
Check how it works before contributing.

For the impatient::
1. Fork the repo and create your branch from `development`.  
   1.1. Rebase onto development if you already have a fork.
2. Edit the files, add new files
3. If you've added code that should be tested, add tests.
5. If you've changed APIs, update/add the documentation.
4. Make sure you follow the Coding Style.
6. Ensure the test suite passes.
7. Create a new branch with a descriptive name for your feature/change
8. Commit changes, push to your fork on GitHub
8. Open a pull request on GitHub (provide a short summary of changes in the title line, with more information in the description field).

*PRO Tip*: Keep your PR [clear and small](https://www.atlassian.com/blog/git/written-unwritten-guide-pull-requests). It would be easier to find someone to review it.

Any contributions will be under the GPL-3.0 License
----------------------
In short, when you submit code changes, your submissions are understood to be under the same [GPL-3.0 License](https://www.gnu.org/licenses/gpl-3.0.html) that covers the project. Feel free to contact the maintainers if that's a concern.

Coding style guides
-------------------

### Python
To maintain the readability of codes, You should closely follow the PEP8 style guide described [here](http://www.python.org/dev/peps/pep-0008/).
You can check your code whether it follows the PEP8 style guide with:

```shell
$ pip install pep8
$ pep8 path/code_to_check.py
```
In addition, most of the modern Python IDEs also have options to show pep8 suggestions.

We use [docstring](https://www.python.org/dev/peps/pep-0257/).

### C++
[TO-DO]


Versioning
----------
We use the [Calendar Versioning](https://calver.org/) scheme.

References
----------
Adapted from several CONTRIBUTING files of other projects:  
· https://github.com/ooda/cloudly/blob/master/CONTRIBUTING.md  
· https://github.com/KAIST-MACLab/PyTSMod/blob/main/CONTRIBUTING.md  

