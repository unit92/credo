---
title: User Manual
---

<style>

.button {
    background-color: #3bbbad;
    color: white;
    text-align: center;
    border: none;
    border-radius: 2px;
    height: 36px;
    padding: 0 16px;
    margin: 0 5px;
    text-transform: uppercase;
    display: inline-block;
    vertical-align: middle;
    box-shadow: 0 2px 2px 0 rgba(0, 0, 0, 0.14), 0 3px 1px -2px rgba(0, 0, 0, 0.12), 0 1px 5px 0 rgba(0, 0, 0, 0.2);
    letter-spacing: normal;
    font-size: 14px;
    line-height: 36px;
}

.tool {
    background-color: #00acc1;
}

.flat {
    background-color: #f0f0f0;
    box-shadow: none;
    color: #343434;
}

.navigation {
    background-color: #37474f;
}

/* @laith turns out they don't sanbox their CSS,
 * it wasn't working because .navbar is the class they
 * used for the actual site navbar :stuck_out_tongue:
 * Ohhhhh, thanks for the info :)
 * * */

</style>


[TOC]

# Introduction

Credo is an online tool for music comparison.

# Terminology

Song

: A piece of music, which allows for a set of differing _editions_.

Edition

: A primary source of a song, provided on Credo by an administrator.

Revision

: A user-created version of a song, created off one or more editions/revisions.

MEI 

: Music Encoding Initiative (MEI) is an encoding created to represent musical documentation . 

  All Credo songs, editions and revisions are written and downloadable as an MEI file.

# Usage

## For Users

### Sign Up

To obtain access to further Credo functionality, access the sign up page using the <span class="button navigation">Sign Up</span> button and enter your details. 


### Login

Access the login page using the <span class="button navigation">Login</span> button and enter your user credentials.


:::warning
The username field validates on your username only, not your email!
:::

:::success
Usernames are <strong><i>case-insensitive!</i></strong>
:::

### Viewing Editions and Revisions

Viewing editions or revisions of a song is done through the song page. By clicking on a song, you are taken to a list of editions and revisions. Editions of a song are listed, and a user's owned revisions are also listed if they are logged in.

By clicking on an edition or revision, the user is taken to a page, displaying the sheet music for the desired selection.

#### Downloading Sheet Music
While viewing an edition or revision, the user is given the option to download the sheet music as an MEI file. To do this, press the <span class="button">Download</span> button.

:::warning
You must be logged in to download sheet music!
:::

### Comparing Pieces

After selecting a song, press the <span class="button">Compare</span> button to begin piece comparison.

Once two editions or revisions have been selected on the comparison page, press the <span class="button">Compare</span> button again to run the comparison algorithm and view the output.

:::warning
You must be logged in to use comparison functionality!
:::

### Revisions

:::warning
You must be logged in to access revision functionality!
:::

#### Creating Revisions

You can create a revision from any edition or any comparison between two editions. Simply press the <span class="button">Make revision</span> button. You will be presented with a prompt for a name for the new revision, and then be directed to the revision editor.

#### Editing Revisions

There are two tools available when editing a revision: the <span class="button tool">Comment</span> tool and the  <span class="button tool">Resolve</span> tool.

Once a user has completed editing, the user may save their changes, using the <span class="button tool">Save</span> button.

##### Commenting

After selecting the <span class="button tool">Comment</span> button, you can click any notation on the displayed music piece to attach a comment to it.

##### Resolving Conflicts
 
After selecting the <span class="button tool">Resolve</span> button, you can click on any bar in the piece to open the resolve tool dialog.

###### Playing a bar
    
Pressing the <span class="button flat">Play</span> button will play the currently open bar as a piano track.

###### Resolving conflicts

To resolve conflicting areas of notation, deselect coloured notation as desired. Press <span class="button flat">Submit</span> in order to complete resolution for the currently selected measure.

###### Layers and switching

For ease of use, you can <span class="button flat">Swap Layers</span> to bring notes behind other notes to the front. This is useful for clicking on notes behind another note.

---

## For Administrators

### Creating Songs and Editions

Once logged in as an administrator, several new buttons will appear.

On the song list page, there will be a <span class="button">Add New</span> button. Clicking on this will bring you to a page in which you can create a new song.

You will be prompted to enter a song name, and a composer. You may either pick from the list of current composers, or create your own by typing in the text field.

:::warning
Songs must be created before editions or revisions can be created!
:::

After you have created a song, you will be brought to the edition/revision list for that song. As it is a newly-created song, there won't be any editions - but you can create more using the <span class="button">Add New</span> button.

On the new edition page, you will be prompted for an edition name, and also to upload an MEI file. After creating a new edition, you will be brought to the edition view page.

### Django Admin Panel

The Django Admin Panel is accessible at https://credo.techlab.works/admin. This admin panel provides granular control over all aspects of user and data management. Most normal functionality does not require use of the admin panel - users can sign up and log in themselves, and you are able to create songs and editions without using the admin panel.

You can refer to the developer guide for information about Credo database models.
