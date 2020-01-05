---
layout: default
nav: assignments
title: [[ assignment.title ]]
---

- Assigned: [[ assignment.dates.assigned | date ]] PST
- Due: [[ assignment.dates.due | datetime ]] PST
- Directory name in your github repository for this homework (case sensitive): `[[ assignment.short ]]`
   - Once you have cloned your `{{ site.data.material.urls.github }}/hw-username` repo, create this `[[ assignment.short ]]` folder underneath it (i.e. `hw-username/[[ assignment.short ]]`).
   - Skeleton code for this assignment is available in `homework_resources/[[ assignment.short ]]`.

## [[ assignment.title ]]

[[ assignment | get_readme ]]
[% for problem in assignment.problems -%]
[% include "template:build/instructions/problem.md" %]
[%- endfor -%]

### Submitting Your Solution

You can submit your homework [here](http://bits.usc.edu/codedrop/?course={{ site.data.material.slugs.site }}&assignment=[[ assignment.short ]]&auth=Google).
Please make sure you have read and understood the [submission instructions]({{ site.url }}/assignments/submission-instructions.html).

**WAIT!** You aren't done yet!
Complete the last section below to ensure you've committed all your code.

### Commit and Re-clone Your Repository

Be sure to add, commit, and push your code in your {{ assignment.short }} directory to your `hw-username` repository.
Now double-check what you've committed, by following the directions below (failure to do so may result in point deductions):

1. Please make sure you have read and understood the [submission instructions]({{ site.url }}/assignments/submission-instructions.html).
1. Go to your home directory: `$ cd ~`
2. Create a `verify` directory: `$ mkdir verify`
3. Go into that directory: `$ cd verify`
4. Clone your hw-username repo: `$ git clone git@github.com:{{ site.data.material.slug.github }}/hw-username.git`
5. Go into your {{ assignment.short }} folder: `$ cd hw-username/{{ assignment.short }}`
6. Recompile and rerun your programs and tests to ensure that what you submitted works.
7. Go to the Assignments page and click on the submission link.
8. Find your full commit SHA (not just the 7 digit summary) and paste the full commit SHA into the textbox on the submission page.
9. Click **Submit via Github**
10. Click **Check My Submission** to ensure what you are submitting compiles and passes any basic tests we have provided.
