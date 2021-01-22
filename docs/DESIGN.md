# k8s.elections' Design 

k8s.elections is operated via GitOps model, just like the other kubernetes projects are operated. The application is designed to keep the flexibilty in mind so that other CNCF and LF project can also make use of this project.

This document helps in understanding the different design aspects of the application, such as:
- [Architecture](#Architecture)
- [Specifications](#specifications)
- [UI Markups](#ui-markups)
- [Workflow](#Workflow)
<!-- - [ERD](#ERD) -->


## Architecture 

The general idea of the application is shown below. A seperate repository - **k8s.elections.meta** is maintained to keep track of all the meta files (`.yaml`) for elections, this repository serves as the single source of truth for the application's operation which is operated by gitops model. All the adminstrative tasks like creation of new elections, updation of voter's list, register of a candidate profile etc will be performed by raising specific pull requests in this repository.

![architecture.png](/static/arch.png)

After rasing a pull request, the gitops-bot will push events to the **k8s.elections** application (flask server) via web hooks. `k8s.elections` server is responsible for conducting the elections, receiving responses and computing the results. 

The voters can only interact (browse/vote elections) with the application only after authenticated by an external OAuth vendor (ex - github, gitlab). The results of these ballots are stored in a MySQL Database running as GCP Service.

## Specifications

The detailed proposed specifications can be found at this [doc](https://docs.google.com/document/d/e/2PACX-1vQ4Z3jOpIsGZHaBy9Xa6me6IyL_rj-JZgAl-xRO-M2KacWhcRexcV3mILjwclsc9QI4ghRfic2ESFtB/pub). 

### UI Markups

The UI markups can be found at this figma [doc](https://www.figma.com/file/Sav9lAC86Vb3vO64sI0xbi/Untitled?node-id=0%3A1)

## Workflow

The workflow of the application is divided in three sections depending on the stage of the election, which are 

### Before election started

This parts is majorly handled with gitops, i.e., mostly adminstrative. Below is an sequence diagram to show the workflow for declare an election and other EO related tasks.

| ![architecture.png](/static/sequence-1.png) |
| ------ |

### Election in progress

The Election officers starts the election, and now the voters can login with their github to view the election info, candidates list, a candidates profile page and then vote.

While the election is running the election officers can view the election stats several times from UI, and closes the election after the voting deadline is over.

| ![architecture.png](/static/sequence-2.png) |
| ------ |
<!-- | ![architecture.png](/static/sequence-diagram.png) |
| ------ | -->

### After Election

After the election ends an EO can see full election results in the web interface (only accessable to EOs), then push public election results to results.md file for voter to see.

An EO can also download a CSV or YAML file of private election results for archiving that Would include same information as the full election results.

| ![architecture.png](/static/sequence-3.png) |
| ------ |