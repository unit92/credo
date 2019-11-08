---
title: Developer Manual
---

[TOC]

# Introduction

Credo is an online tool for music comparison.

## Quick Setup

:::info
Use of a Python virtualenv is recommended.
:::

Install dependencies:
```bash
$ pip install -r dev-requirements.txt --user
$ pip install -r ci-requirements.txt --user
$ pip install -r requirements.txt --user
```

Install git hooks:
```bash
$ pre-commit install
```

Set up environment variables:
```bash
$ cp .env.example .env
```

To run the containerised database:
```bash
$ cd docker
$ docker-compose up
```
:::info
This requires `docker-compose` to be installed.
:::

To run the Django server:
```bash
$ cd src
$ python manage.py runserver
```

## Testing

All unit tests should be located in `./src/tests/*`. Test discovery will find any tests in a file named `test*.py` in the current working directory.

To run tests:
```bash
$ python -Wa manage.py test
```
The `-Wa` flag tells Python to display deprecation warnings for Postgres, etc.

## Terminology

Song

: A piece of music, which allows for a set of differing _editions_.

Edition

: A primary source of a song, provided on Credo by an administrator.

Revision

: A user-created version of a song, created off one or more editions/revisions.

MEI 

: [Music Encoding Initiative (MEI)](https://music-encoding.org/) is an encoding created to represent musical documentation. 

  All Credo songs, editions and revisions are written and downloadable as an MEI file.

# System Overview

## Backend

Credo's backend is a Django app hosted on an AWS server. It is written for Python 3.7 upward, as we use newer features such as f-strings and type annotations.

Additionally, the backend utilises a custom made music comparison engine, designed to be modular, should a different algorithm for comparing music be desired in the future.

All Python code is written to be compliant to PEP-8.

## Frontend

The frontend consists of HTML, CSS, and JavaScript, served by the Django server. [Materialize](https://materializecss.com) is used and served statically. [Verovio Toolkit](https://www.verovio.org/javascript.xhtml) is a JavaScript library used to render MEI into an SVG.

A custom JS library is Credo Toolkit. This file wraps around Verovio Toolkit to expose and make the required functionality of Verovio Toolkit more straightforward for the intended uses. Additionally, it serves to drive and handle interactions:
* Requesting MEI files to render
* Requesting comments for a revision and rendering them onto the SVG
  * Escaping HTML characters in comments
* Driving the toolbar on the revision page
* Resolving conflicting measures in revisions
* Naming and sending a request to make a new revision

All in-house JavaScript is written to adhere to [Standard JS](https://standardjs.com/).

# Django

## Models

### Database Schema

![Database Schema](https://i.imgur.com/ZVm1EaB.png)

:::info
The MEI object has a post-save hook that calls our normalization function on any uploaded MEI file.
:::

It is important to note that we do not interface with the database directly (i.e. through PostgreSQL); we interact with it through the Django ORM. This can be accessed through the `manage.py` Django interface:

```bash
$ python3 manage.py shell
```

## Routes and Views

The following is a table listing all routes with their associated methods and views, and what level of authentication is required to access the route.

| Route                      | Method | View                          | Description                                     | Login Conditions           |
| ---                        | ---    | ---                           | ---                                             | ---                        |
| `/`                        | `GET`  | `index()`                     | _Page_ - Homepage of Credo                      | Anonymous                  |
| `/songs`                   | `GET`  | `song_list()`                 | _Page_ - List of songs                          | Anonymous                  |
| `/songs/<id>`              | `GET`  | `song()`                      | _Page_ - Editions and revisions on a song       | Anonymous                  |
| `/songs/<id>/compare`      | `GET`  | `song_compare_picker()`       | _Page_ - Pick editions and revisions to compare | Logged in                  |
| `/editions/<id>`           | `GET`  | `edition()`                   | _Page_ - Render an edition                      | Logged in                  |
| `/revisions/<id>/comment`  | `POST` | `add_revision_comment()`      | _API_ - Add a comment to a revision             | Logged in                  |
| `/revisions/<id>`          | `GET`  | `RevisionView()`              | _Page_ - Render a revision                      | Logged in and own revision |
| `/revisions/<id>`          | `POST` | `RevisionView()`              | _API_ - Save a revision                         | Logged in and own revision |
| `/revisions/<id>/comments` | `GET`  | `revision_comments()`         | _API_ - List revision comments                  | Logged in and own revision |
| `/mei/<id>`                | `GET`  | `mei()`                       | _API_ - Get MEI data                            | Anonymous                  |
| `/compare`                 | `GET`  | `compare()`                   | _Page_ - Compare two editions/revisions         | Logged in                  |
| `/diff`                    | `GET`  | `diff()`                      | _API_ - Run the diff algorithm                  | Logged in                  |
| `/merge`                   | `POST` | `merge_measure_layers_json()` | _API_ - Merge two measures together             | Logged in                  |
| `/revise`                  | `GET`  | `make_revision()`             | _Page_ - Create a revision                      | Logged in                  |
| `/signup`                  | `GET`  | `signup()`                    | _Page_ - Signup page                            | Anonymous                  |
| `/signup`                  | `POST` | `signup()`                    | _API_ - Sign up a user                          | Anonymous                  |
| `/editions/new`            | `GET`  | `NewEditionView()`            | _Page_ - Create a new edition                   | Administrator              |
| `/editions/new`            | `POST` | `NewEditionView()`            | _API_ - Create a new edition                    | Administrator              |
| `/songs/new`               | `GET`  | `NewSongView()`               | _Page_ - Create a new song                      | Administrator              |
| `/songs/new`               | `POST` | `NewSongView()`               | _API_ - Create a new song                       | Administrator              |
| `/revisions/<id>/download` | `GET`  | `download_revision()`         | _API_ - Download a revision MEI                 | Logged in                  |
| `/editions/<id>/download`  | `GET`  | `download_edition()`          | _API_ - Download a edition MEI                  | Logged in                  |
| `[404 page]`               | `GET`  | `page_not_found()`            | _Page_ - 404 page                               | Anonymous                  |
| `[5XX page]`               | `GET`  | `server_error()`              | _Page_ - 5XX page                               | Anonymous                  |
| `/editions/wildwebmidi`    | `GET`  | `wildwebmidi_data()`          | _API_ - Return MIDI data for playback           | Anonymous                  |

# Deployment

## Deployment Stack

The deployment stack is ever so slightly different to the development stack, as it is unsafe to run Django in development mode on a publicly accessible server.

We use nginx to serve static content, an example configuration is provided at: `./config/nginx/credo.conf`.

We use gunicorn as the production Django server, this is not required for developers locally however. Gunicorn connects to nginx over a unix socket.

We currently run the Postgres server in a docker container on the server, however you may easily migrate this to AWS RDS in the future if it is found to be too slow. 

The Postgres docker container, dockerd, gunicorn and nginx are all started via systemd. Nginx comes with a default systemd unit so there was no need to create any configuartions for this, however the others did require configuration and have been included here: `./deployment/config/systemd`

## Continuous Deployment
:::    warning
This setup is not recommended for future development
:::

The deployment is done automatically through a cronjob that runs every 5 minutes. The script is located at `./deployment/restart-if-updated.sh`. The script itself is heavily commented, and is intended to be run in a cronjob. In essence the bash script will pull from the repo at a specified branch (or develop if none is specified). If there are any updates from origin, it will merge them in and rebuild the static content, install any new dependencies, run any pending migrations and restart the server. This is quite janky, I would propose that in future developers move away from this and use something like AWS CodeDeploy. Also note that the server has its public SSH key set up on Bitbucket as a read only key, allowing us to clone the repo on the server without having to hard code any credentials in the script. A similiar set up can be achived on github if required.

This works fine the majority of the time, there is however a bit of a hickup as there is no way for us to currently automatically update the .env file, so someone manually has to SSH in and do this. I would suggest setting environment variables thorugh AWS Parameter Store in future, or perhaps there is a better solution involving AWS CodeDeploy.

# Continuous Integration (Pipelines)

We do our CI through Bitbucket Pipelines, they won't work with Github Actions, or any other CI platform you choose. See `./bitbucket-pipelines.yml` for more info. In essence every PR has to pass a build which consists of:

* Installing the runtime dependencies
* Installing the CI dependencies
* Setting up the environment
* Running all tests with coverage
* Generating a coverage report

The tests also run Postgres in a docker container, there should be a way to do this with your CI platform of choice, if not, you can start the docker container manually.


# Music Comparison Engine

The music comparison engine is designed to follow the strategy pattern, so new comparison algorithms can be created and swapped out as desired.

## Overview by Class

### `ComparisonStrategy`

#### `compare_meis`

Defines a method `compare_meis` which accepts two MEI models, and calls `compare_trees`, the main method that is to be implemented by any concrete comparison strategy.

#### `compare_trees`

`compare_trees` should accept two `lxml.etree.ElementTrees` representing MEI files, `a` and `b`. It should return a tuple of `lxml.etree.ElementTrees`, where the first tree represents the difference of `a` and `b`, the second is `a`, containing any additional modifications made to it as needed, and the third is `b`, containing any additional modifications.

### `TreeComparison`

This class implements the `compare_trees` method of `ComparisonStrategy`.

#### `compare_trees`

Trees are converted to intermediate form, then compared using the `__get_diff_tree` method, returned to plain MEI form, and then their IDs are regenerated to aid the resolve tool on the front end.

#### `__get_diff_tree`
The `__get_diff_tree` method accepts two 
`lxml.etree.ElementTrees` `a` and `b`. These trees are given to the main method of `xmldiff`, which returns a list of actions required to turn tree `a` into tree `b`. The `TrackedPatcher` class is used to generate two modified versions of `a` and `b`, keeping track of which nodes in `a` were moved/inserted/deleted, and which node in `b` they correspond to. This allows colours and visibilities of elements to be modified only for those elements that had move/inserte/delete operations applied to them. Note that colours are applied to an entire chord or beam if any of the elements in the chord or beam were modified, as these elements are treated as groups by the front end.

The following functionality is important to note, since a lot of the front end functionality in the `Credo Toolkit` relies on colours and visibility of nodes for its operations:

- All nodes in the `b_modded` tree are hidden by default, unless modifications were applied to them. This is to avoid doubling up on rendering of notes that are common to both `a` and `b`.

`__naive_layer_merge` is then called to create the diff tree, and the method returns the `diff`, `a` and `b` trees.

#### `__naive_layer_merge`

Once the colour/visibility attributes on the `a_modded` and `b_modded` trees have been updated, these two trees are merged into one, where corresponding layers from `a_modded` and `b_modded` are inserted into the new tree under the same measure tag. This allows the diff to be rendered properly in Verovio.

This method makes a lot of assumptions and might need to be updated in the future, but works well as a proof of concept.

Note that layers that came from `a_modded` should have an `xml:id` of the format `m-a[0-9]+`, and layers that came from `b_modded` should have an `xml:id` of the format `m-b[0-9]+`. This is essential as the Credo Toolkit uses this to determine which layers came from which source during resolution. Also note that if layers are *corresponding*, i.e. they have the same `n` value, then the number after the `a` or the `b` in their `xml:id` should be identical.


# Credo Toolkit

Credo Toolkit is a custom-written JavaScript file to drive Credo's interactions.

## Usage Guide

The following script inclusions are required for Credo Toolkit:
```htmlmixed=
<script
  src="{% static 'credo/verovio/verovio-toolkit.js' %}"
  type="text/javascript">
</script>
<script
  src="{% static 'credo/credo-toolkit.js' %}"
  type="text/javascript">
</script>
```

Additionally, if MIDI playing is desired (like on the revision pages), the following imports are also required:
```htmlmixed=
<script
    src="https://ajax.googleapis.com/ajax/libs/jquery/1.12.0/jquery.min.js"
    type="text/javascript">
</script>
<script
  src="{% static 'credo/midi/wildwebmidi.js' %}"
  type="text/javascript">
</script>
<script
  src="{% static 'credo/midi/midiplayer.js' %}"
  type="text/javascript">
</script>

```
The above static files are:
* jQuery
* [Wild Web Midi](https://github.com/zz85/wild-web-midi)
* Midiplayer.js
:::info
This is the only place jQuery is used.
:::

Then, to use Credo Toolkit:
```htmlmixed=
<script>
  const toolkit = new CredoToolkit(
    '{{ meiUrl }}',
    null,
    null,
    'renderDiv'
  )
  toolkit.render()
</script>
```

The arguments the constructor takes are:
1. A URL from which to load the MEI file.
2. A URL from which to load comments (optional, used in revisions).
3. A URL to invoke during measure resolution (optional, used in revisions).
4. An ID of a `<div>` in which to insert any rendered music.
5. A URL to invoke when saving a revision (optional, used in revisions).

## Overview

### Rendering MEI

As a whole, rendering is handled by an asynchronous `render` function, which requests and stores the MEI, if it is not already loaded, and calls `renderMei`.

`renderMei` finds the desired `<div>` in which to render the MEI, renders the MEI using Verovio Toolkit, and inserts the output SVG into the desired element.

### Revisions

#### Toolbar

Credo Toolkit drives the interactions with the toolbar, with an event listener on the tools used to switch tools depending on which button in the toolbar is pressed, and updates the toolbar UI to reflect this.

The current tool affects which functions are invoked when a sheet music element is clicked.

#### Comments

Comments are handled and rendered in the `render` function, which requests and renders comments from a given URL. Comments are rendered onto SVG sheet music by getting the notation with a matching ID, then adding a comment SVG to said notation, which has a Materialize tooltip containing the comment message. Note that this tooltip had to be manually positioned using JavaScript.

If a note is clicked upon while in commenting mode, a modal is presented, where you can add, edit, or remove a comment.

#### Resolution

The resolution tool presents a modal containing only the measure that the user wishes to resolve. From there, event listeners on this measure capture and maintain a state of notes which are desired to be kept and removed.

#### Saving

Saving simply makes a request to an endpoint which takes the MEI and comments in a JSON object.

#### Downloading

Downloading makes a request to an endpoint which downloads the MEI for the edition or revision in question. Note that, for revisions, you can only download the revision once all conflicts have been resolved.

## By Method

### Constructor

Constructs the Credo Toolkit.

#### Arguments

| Name | Type | Description |
| ---  | ---  | ---         |
| meiUrl | string | The URL of the MEI file we wish to render. |
| commentsUrl | string or null | The URL of any associated comments, can be null to indicate no comments. |
| resolutionUrl | string or null | The URL used for merging layers within a measure, can be null to indicate no merge support. |
| renderDiv | string | The ID of the div to which we wish to render. |
| saveUrl | string or null | Optional. The URL to POST when saving revisions. |

#### Description

The Credo Toolkit constructor is responsible for the following:
* Initialising event listeners once the DOM has loaded
  * Comment modal functionality
  * Resolve modal functionality
    * The "Play" button
    * Swapping resolve layers
    * Selecting/deselecting notes
  * The "Make Revision" button
  * The naming modal for making revisions
  * The modal to show while saving a revision
  * The "Save" button
  * Revision toolbar
* Initialising a Verovio Toolkit instance
* Getting the CSRF token from a cookie and storing it

### `scoreInteractionListener`

Listens to click events on the score, and performs behaviour appropriate to the current editing mode.

#### Arguments

| Name | Type | Description |
| ---  | ---  | ---         |
| event | Event | A HTML DOM event. |

#### Return Value

`void`

#### Description

Invokes `commentEventListener`, `resolveEventListener`, with `event`, or neither, depending on the state of `this.currentToolMode`.

### `resolveEventListener`

Responds to the click event by reacting as if in resolve mode.

#### Arguments

| Name | Type | Description |
| ---  | ---  | ---         |
| event | Event | A HTML DOM event. |

#### Return Value

`void`

#### Description

Using `event.target`, this method attempts to go upwards through the DOM until it reaches an element marked as a measure in the `classList`. If it doesn't find a measure, nothing occurs. If it does find a measure, it opens the resolve modal, using the ID of the measure.

### `openResolveModal`

Opens up the resolve modal for a given measure.

#### Arguments

| Name | Type | Description |
| ---  | ---  | ---         |
| targetId | string | The ID of the measure to resolve. |

#### Return Value

`void`

#### Description

Populates the contents of the resolve modal with a rendered MEI of the measure in question. Once it has done that, the resolve modal is opened.

### `resolveNote`

Attempts to resolve the notation clicked upon.

#### Arguments

| Name | Type | Description |
| ---  | ---  | ---         |
| event | Event | A HTML DOM event. |

#### Return Value

`void`

#### Description

Maintains a list of notations which are eliminated, and toggles the state of the notation clicked upon. Also updates the visuals of the note to reflect this change, changing the alpha value to be transparent.

### `submitMeasureResolution`

Propagates changes to the measure to the full piece.

#### Return Value
`Promise<void>`: A promise indicating completion of the attempt to propagate the changes.

#### Description

Removes notation in the resolve modal that was marked as to remove by the user, then makes a request to the server to complete measure resolution, takes the result, and if it is resolved, updates the measure in the piece locally, and closes the modal. If the response indicates the measure is not resolvable, prompt the user with an error message.

### `playSnippet`

Converts the snippet open in the resolve tool into MIDI and plays it.

#### Return Value

`void`

#### Description

This method uses jQuery.
Forms a MIDI datablock by invoking `renderToMIDI` on Verovio Toolkit and uses MIDI Player to play the resulting song.

### `swapResolutionLayers`

Swaps the order in which the diff layers are rendered for resolution.

#### Return Value

`void`

#### Description

Uses a object to track layers and DOM manipulation to ensure all notes of a certain colour are re-rendered in reverse order in which they appear.

### `clearResolveModal`

Clears the resolve modal.

#### Return Value

`void`

### `generateResolveMei`

Generates the MEI to display in the resolve modal.

#### Arguments

| Name | Type | Description |
| ---  | ---  | ---         |
| measure | Node | The measure to render. |

#### Return Value
`string`: The generated MEI as a string.

#### Description

In order to render a single measure of a piece, it needs to be made into its own MEI encoding. This is done by using a single-measure template, taking metadata from the piece's MEI, and inserting the measure of the MEI into the body.

### `nameSpaceResolver`

Namespace resolver for parsing MEI Document.

#### Arguments

| Name | Type | Description |
| ---  | ---  | ---         |
| prefix | string | The namespace prefix. |

#### Return Value

`string` or `null`: The resolved namespace.

#### Description

Namespace resolution is required for navigating the MEI XML using XPath.

### `commentEventListener`

Reacts to the click event by reacting as if in comment mode.

#### Arguments

| Name | Type | Description |
| ---  | ---  | ---         |
| event | Event | A HTML DOM event. |

#### Return Value

`void`

#### Description

This method gets the notation clicked on in the DOM, and opens a comment modal to receive text input. If a comment already exists for the clicked notation, populate the textarea with the comment text.

### `updateCommentFromModal`

Updates the comments from the modal.

#### Return Value

`void`

#### Description

Updates its internal comments object. Gets the text value from the comment modal's text area, and using the ID of the notation clicked on, add, update, or delete the comment associated with that notation, depending on whether the comment existed already, and if the text area is empty or not.

### `loadMei`

Loads the MEI from the URL.

#### Return Value

`Promise<string>`: A promise resolving to the MEI.

### `loadAndStoreMei`

Loads the MEI, and stores it on the object and the Verovio toolkit.

#### Return Value

`Promise<void>`: Resolves upon completion.

### `loadComments`

Loads the comments from the URL.

#### Return Value

`Promise<Object[]>`: A promise resolving to a series of comments.

### `loadAndStoreComments`

Loads the comments, and saves them to a member variable.

#### Return Value

`Promise<void>`: Resolves upon completion.

### `improveClickHitBoxes`

Goes over a rendered SVG in the renderDiv, and proceeds to make notation more easily clickable.

#### Return Value

`void`

#### Description

:::warning
This only affects users on Chromium.
:::
Finds every interactable notation in the rendered SVG, and adds an attribute to them, that changes how they listen to click events. The attribute set is `pointer-events="bounding-box"`, and prevents holes, such as those in minims and semibreves, from being clickable.

### `render`

Renders the MEI file, and any comments associated.

#### Return Value

`Promise<void>`

#### Description

Loads the MEI, requesting it if not already stored and renders the MEI through Verovio Toolkit. It inserts the rendered SVG into the designated render target, and calls `improveClickHitboxes`. Then, it loads comments if they haven't been loaded before, and renders those onto the SVG.

### `renderDiff`

:::danger
This method is no longer used.
:::

Renders the MEI diffs, to a list of inline SVGs.

### `renderMei`

Renders the given MEI to an inline SVG to be contained in the element specified at construction.

#### Return Value

`void`

#### Description

This method neatly wraps around Verovio Toolkit, to render the MEI to an SVG, and insert it into the DOM at the designated render target.
Used in `render`.

### `renderComments`

Renders all comments.

#### Return Value

`void`

#### Description

Renders the comment icon for each comment, and then adjusts Materialize tooltips for all comments.

### `renderCommentIcon`

<!-- Short description here. Rip from docstring if present. -->

#### Arguments

| Name | Type | Description |
| ---  | ---  | ---         |
|      |      |             |

#### Return Value

#### Description

<!-- Long description here. -->

### `addComment`

Renders the comment icon onto the rendered SVG. Also does some tooltip text setup.

#### Arguments

| Name | Type | Description |
| ---  | ---  | ---         |
| elementId | string | The ID of the MEI element to which we attach the comment icon. |
| text | string | The comment text.

:::info
These two arguments are destructured from a single array argument.
:::

#### Return Value

`void`

#### Description

This method inserts a comment SVG into the DOM, as a child of the notation with the given element ID. It performs some positioning logic to do this. Additionally, it sets an attribute on the comment SVG, `data-tooltip`, which is used by Materialize to determine the text content of tooltips.

### `updateComment`

Updates an already existing comment.

#### Arguments

| Name | Type | Description |
| ---  | ---  | ---         |
| elementId | string | The ID of the MEI element whose comment we wish to update.
| text | string | The comment text.

#### Return Value

`void`

#### Description

This method updates the internal object maintaining comments. It finds the element in question, finds the comment SVG on that element, and updates its `data-tooltip` attribute to use the new comment text.

### `deleteComment`

Delete an existing comment.

#### Arguments

| Name | Type | Description |
| ---  | ---  | ---         |
| elementId | string | The MEI element whose comment we wish to delete. |

#### Return Value

`void`

#### Description

Removes the entry for the given comment in the comment object, and removes the comment SVG for that element from the DOM.

### `handleTooltips`

Handles the tooltips' positioning and rendering.

#### Return Value

`void`

#### Description

This method invokes Materialize's tooltip initialisation. Additionally, for each comment, it attaches a tooltip positioning listener.

### `attachTooltipPositioningListener`

Attaches a listener to position the tooltip popover as it renders.

#### Arguments

| Name | Type | Description |
| ---  | ---  | ---         |
| elementId | string | The ID of the MEI element whose tooltip we wish to position. |

#### Return Value

`void`

#### Description

This method attaches an event listener to every comment SVG icon, which is triggered upon mouseover of the comment icon.

Whenever this event listener fires, it positions the tooltip rectangle that appears such that it appears below the comment icon, and centred over it (bounded by the screen dimensions, though).

This is done on every mouse over instead of just once in the case that the window size is changed since the last mouse over.

:::warning
While Materialize tooltips normally self-position, by invoking them from within an SVG, this functionality was lost, and hence we must position them ourselves.
:::

### `getNotation`

Gets the commentable notation from the event target.

#### Arguments

| Name | Type | Description |
| ---  | ---  | ---         |
| event | Event | The event for which we want to find the relevant notation. |

#### Return Value

`Element | null`: The clickable note element. Null if no clickable notation found.

#### Description

This method is responsible for determining which "clickable" notation was clicked.

Starting from an element in the DOM, it traverses upwards through the DOM tree until it finds an element that is directly represented in the MEI.

:::info
An element is "clickable" if it's ID also appears in the MEI file. That is, it directly corresponds to a piece of MEI notation (not an SVG path, stroke, etc.).
:::

:::info
All clickable notation has an ID matching the following regex: `m-[0-9]*`.
:::

### `saveRevision`

Saves the revision to the backend.

#### Return Value

`Promise<void>`: Resolves upon completion.

#### Description

This makes a request to the server, containing the updated MEI and any associated comments.

While saving, it also manages presenting a modal to give the user feedback; it could be saving, finished saving successully, or failed.

### `updateCurrentToolMode`

Depending on what toolbar button was pressed, update the `currentToolMode` property on this object.

#### Arguments

| Name | Type | Description |
| ---  | ---  | ---         |
| event | Event | A DOM event. |

#### Return Value

`void`

#### Description

This listener looks for an ID on the button that was pressed in the toolbar. While finding that, it also sets that button to appear active, and sets the other buttons to appear inactive.

An internal class variable, `currentToolMode` is also updated to reflect the new interaction mode.

### `jsonRequest`

Makes a GET request, and parses the response as JSON.

#### Arguments

| Name | Type | Description |
| ---  | ---  | ---         |
| url | string | The URL to request. |

#### Return Value

`Promise<Object>`: The JSON object received from the response.

#### Description

Generates and sends an HTTP request, and wraps around XHTTP's callback interface to provide a Promise interface.

### `getCookie`

Gets the value of a cookie with given name.

#### Arguments

| Name | Type | Description |
| ---  | ---  | ---         |
| name | string | The cookie whose value we wish to retrieve. |

#### Return Value

`string | null`: The cookie value. `null` if not found.

#### Description

Wraps around `document.cookie` to provide easier access to cookies.

### `escapeHtmlCharacters`

Takes in a string and escapes HTML characters.

#### Arguments

| Name | Type | Description |
| ---  | ---  | ---         |
| text | string | The text to escape. |

#### Return Value

`string`: The escaped text.

#### Description

Performs a series of text substitutions to escape characters used in HTML. Used to make comment text safe.

# References
* [Django](https://docs.djangoproject.com/en/2.2/)
* [Verovio JS Toolkit](https://www.verovio.org/javascript.xhtml)
* [Materialize](https://materializecss.com/)
* [Wild Web Midi](https://github.com/zz85/wild-web-midi)
* [Midiplayer.js](https://github.com/rism-ch/midi-player/)
* [XMLdiff](https://xmldiff.readthedocs.io/en/stable/)
