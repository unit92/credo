/**
 * This class wraps around the functionalities of the Verovio toolkit, and
 * presents them in a way that is tailored to our use case. We also extend upon
 * its rendering functionality to deliver our own functionality, in music
 * commenting.
 */

class CredoToolkit {
  // class variables
  meiUrl
  commentsUrl
  renderDiv

  mei
  comments

  commentModalInstance
  // ID of the thing on which we are commenting
  commentModalId

  savingModalInstance

  verovioToolkit

  // toolbar stuff
  tools

  // editing mode
  currentToolMode = 'inspect'

  // Sourced from https://material.io/resources/icons/
  commentSvg = `
    <svg class="tooltipped" data-position="bottom" xmlns="http://www.w3.org/2000/svg" width="480" height="480" viewBox="0 0 24 24">
      <path d="M21.99 4c0-1.1-.89-2-1.99-2H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h14l4 4-.01-18zM18 14H6v-2h12v2zm0-3H6V9h12v2zm0-3H6V6h12v2z" fill="indigo" />
      <path d="M0 0h24v24H0z" fill="transparent"/>
    </svg>
 `

  // used for saving revisions
  csrftoken

  /**
   * Constructs the Credo Toolkit.
   *
   * @param {string} meiUrl The URL of the MEI file we wish to render.
   * @param {string} commentsUrl The URL of any associated comments, can be
   * null to indicate no comments.
   * @param {string} renderDiv The ID of the div to which we wish to render.
   * @param {string} saveUrl Optional. The URL to POST to when saving revisions.
   */
  constructor (meiUrl, commentsUrl, renderDiv, saveUrl) {
    this.meiUrl = meiUrl
    this.commentsUrl = commentsUrl
    this.renderDiv = renderDiv
    this.saveUrl = saveUrl

    this.verovioToolkit = new verovio.toolkit()

    // initialise the comment modal
    document.addEventListener('DOMContentLoaded', () => {
      const modals = document.querySelectorAll('.modal#comment-modal')
      M.Modal.init(modals)
      this.commentModalInstance = M.Modal
        .getInstance(document.getElementById('comment-modal'))
    })

    // initialise the saving modal if there is a saveUrl
    if (saveUrl) {
      const modals = document.querySelectorAll('.modal#saving-modal')
      M.Modal.init(modals)
      this.savingModalInstance = M.Modal
        .getInstance(document.getElementById('saving-modal'))
    }
    
    // attach the note grabbing listener to the event div
    document.getElementById(renderDiv)
      .addEventListener('click', this.scoreInteractionListener.bind(this))

    // attach a comment submitting method to the submit button in the modal
    const commentModalSubmit = document.getElementById('comment-modal-submit')
    if (commentModalSubmit) {
      commentModalSubmit.addEventListener('click', this.updateCommentFromModal.bind(this))
    }

    // set up the toolbar listening, if applicable
    this.tools = document.getElementById('tools')
    const saveButton = document.getElementById('saveButton')

    if (this.tools) {
      // attach an event listener to handle tool switching
      this.tools.addEventListener(
        'click',
        this.updateCurrentToolMode.bind(this)
      )
    }

    if (saveButton) {
      saveButton.addEventListener(
        'click',
        this.saveRevision.bind(this)
      )
    }

    // get the CSRF token
    this.csrftoken = getCookie('csrftoken')
  }

  /**
   * Listens to click events on the score, and performs behaviour appropriate to
   * the current editing mode.
   *
   * @param {Event} event A HTML DOM event.
   */
  scoreInteractionListener (event) {
    if (this.currentToolMode === 'comment') {
      this.commmentEventListener(event)
    }
  }

  /**
   * Reacts to the click event by reacting as if in comment mode.
   *
   * @param {Event} event A HTML DOM event.
   */
  commmentEventListener (event) {
    // get the notation being clicked on, do nothing if nothing found
    const notation = this.getNotation(event)
    if (!notation) {
      return
    }

    // TODO: things with the current note
    this.commentModalId = notation.id
    document.getElementById('comment-modal-text').value =
      this.comments[this.commentModalId] || ''
    this.commentModalInstance.open()
  }

  /**
   * Updates the comments from the modal.
   */
  updateCommentFromModal () {
    const alreadyExisting = !!this.comments[this.commentModalId]

    const commentTextElement = document.getElementById('comment-modal-text')

    if (!commentTextElement.value && !alreadyExisting) {
      this.commentModalInstance.close()
      return
    }

    this.comments[this.commentModalId] = commentTextElement.value

    if (alreadyExisting) {
      // if there is a text value, update it
      if (this.comments[this.commentModalId]) {
        this.updateComment(
          this.commentModalId,
          this.comments[this.commentModalId]
        )
      } else {
        // delete it, there is no comment text
        this.deleteComment(this.commentModalId)
      }
    } else {
      this.addComment(this.commentModalId, this.comments[this.commentModalId])
    }

    this.commentModalInstance.close()
  }

  /**
   * Loads the MEI from the URL.
   *
   * @return {Promise<string>} A promise resolving to the MEI.
   */
  loadMei () {
    return jsonRequest(this.meiUrl)
      .then(json => atob(json.content.mei.detail))
  }

  /**
   * Loads the MEI, and stores it on the object  and the Verovio toolkit.
   *
   * @return {Promise<void>} A promise to resolve upon completion.
   */
  loadAndStoreMei () {
    return this.loadMei()
      .then(mei => {
        this.mei = mei
        this.verovioToolkit.loadData(mei)
      })
  }

  /**
   * Loads the comments from the URL.
   *
   * @return {Promise<Object[]>} A promise resolving to a series of comments.
   */
  loadComments () {
    return jsonRequest(this.commentsUrl)
  }

  /**
   * Loads the comments, and saves them to a member variable.
   *
   * @return {Promise<void>} A promise to resolve upon completion.
   */
  loadAndStoreComments () {
    return this.loadComments()
      .then(comments => {
        this.comments = comments
      })
  }

  /**
   * Renders the MEI file, and any comments associated.
   */
  async render () {
    // load the MEI if it hasn't been loaded yet
    if (!this.mei) {
      await this.loadAndStoreMei()
    }

    // render the MEI
    this.renderMei()

    if (this.commentsUrl) {
      // if there are comments, load the comments
      if (!this.comments) {
        await this.loadAndStoreComments()
      }

      this.renderComments()
    } else {
      this.comments = {}
    }
  }

  /**
   * Renders the MEI diffs, to a list of inline SVGs.
   */
  async renderDiff () {
    const meiJson = await jsonRequest(this.meiUrl)
    const childDivs = Array.from(document.querySelectorAll(`#${this.renderDiv} > div`))
    childDivs.forEach((div, index) => {
      if (index === 0) {
        const diff = atob(meiJson.content.diff.detail)
        div.innerHTML = this.verovioToolkit.renderData(diff, {svgViewBox: true, adjustPageHeight: true})
      } else {
        const source = atob(meiJson.content.sources[index - 1].detail)
        div.innerHTML = this.verovioToolkit.renderData(source, {svgViewBox: true, adjustPageHeight: true})
      }
    })
  }

  /**
   * Renders the given MEI to an inline SVG to be contained in the element
   * specified at construction.
   */
  renderMei () {
    const renderElement = document.getElementById(this.renderDiv)
    this.verovioToolkit.loadData(this.mei)
    renderElement.innerHTML = this.verovioToolkit.renderData(
          this.mei,
          {
              svgViewBox: true,
              adjustPageHeight: true,
          }
    )
  }

  renderComments () {
    Object.entries(this.comments)
      .forEach(this.renderCommentIcon.bind(this))

    this.handleTooltips()
  }

  /**
   * Renders the comment icon onto the rendered SVG. Also does some tooltip text
   * setup.
   *
   * @param {string} elementId The ID of the MEI element to which we attach the
   * comment icon.
   * @param {string} text The comment text.
   */
  renderCommentIcon ([elementId, text]) {
    // get the element to which we want to attack the comment
    const element = document.getElementById(elementId)
    const position = element.getBBox()

    element.innerHTML += this.commentSvg

    // get the SVG for the comment
    const commentElement = element.children[(element.children.length - 1)]
    commentElement.setAttribute('x', position.x - 350)
    commentElement.setAttribute('y', position.y)

    // set the comment text
    commentElement.setAttribute('data-tooltip', text)
  }

  /**
   * Adds a new comment.
   *
   * @param {string} elementId The MEI element upon which we wish to add a
   * comment.
   * @param {string} text The comment text.
   */
  addComment (elementId, text) {
    this.comments[elementId] = text

    this.renderCommentIcon([elementId, text])

    this.handleTooltips()
  }

  /**
   * Updates an already existing comment.
   *
   * @param {string} elementId The MEI element whose comment we wish to update.
   * @param {string} text The new comment text.
   */
  updateComment (elementId, text) {
    this.comments[elementId] = text

    // get the element
    const element = document.getElementById(elementId)

    // get the comment on the element
    const commentElement = element.children[(element.children.length - 1)]

    commentElement.setAttribute('data-tooltip', text)

    this.handleTooltips()
  }

  /**
   * Deletes an existing comment.
   *
   * @param {string} elementId The MEI ID whose comment we wish to delete.
   */
  deleteComment (elementId) {
    delete this.comments[elementId]

    // get the element
    const element = document.getElementById(elementId)

    // get the comment on the element
    const commentElement = element.children[(element.children.length - 1)]

    // remove it
    commentElement.remove()

    this.handleTooltips()
  }

  /**
   * Handles the tooltips' rendering and positioning.
   */
  handleTooltips () {
    // render the tooltip showing the comment text
    M.Tooltip.init(document.querySelectorAll('.tooltipped'))

    Object.entries(this.comments)
      .forEach(this.attachTooltipPositioningListener.bind(this))
  }

  /**
   * Attaches a listener to position the tooltip popover as it renders.
   *
   * @param {string} elementId The ID of the MEI element whose tooltip we wish
   * to position.
   */
  attachTooltipPositioningListener ([elementId]) {
    // get the tooltip element
    const notationElement = document.getElementById(elementId)
    const commentIcon = notationElement
      .children[notationElement.childElementCount - 1]
    const tooltipElement = M.Tooltip.getInstance(commentIcon).tooltipEl

    commentIcon.addEventListener('mousemove', () => {
      const notationElement = document.getElementById(elementId)
      const commentIcon = notationElement
        .children[notationElement.childElementCount - 1]

      const position = commentIcon.getBoundingClientRect()
      let xPosition = position.x -
        tooltipElement.getBoundingClientRect().width / 2 +
        commentIcon.getBoundingClientRect().width / 2
      if (xPosition < 0) {
        xPosition = 0
      }
      tooltipElement.style.marginLeft = `${xPosition}px`
      tooltipElement.style.marginTop = `${position.y + 20 + (window.pageYOffset || 0)}px`
    })
  }

  /**
   * Gets the commentable notation from the event target. This method will read
   * the target and proceed upward until it finds an element with tag structure
   * 'm-[0-9]*'.
   *
   * @param {Event} event The event for which we want
   * @return {DOMElement} The clickable note element. Returns null if none
   * found.
   */
  getNotation (event) {
    let element = event.target
    while (!element.id || !element.id.match(/m-[0-9]*/)) {
      element = element.parentElement
      if (element.id === this.renderDiv) {
        return null
      }
    }

    return element
  }

  /**
   * Save revision by making a request to the server, giving the revision ID
   * that we are saving over.
   */
  saveRevision () {
    // no saving URL, nothing to do here
    if (!this.saveUrl) {
      return
    }

    const savingModalInstance = this.savingModalInstance

    savingModalInstance.el.innerHTML = `
      <div class="modal-content">
        <h4>Saving</h4>
        <div class="progress">
          <div class="indeterminate"></div>
        </div>
      </div>
    `

    savingModalInstance.open()


    return new Promise((resolve, reject) => {
      const xhttp = new XMLHttpRequest()
      xhttp.onreadystatechange = function () {
        if (this.readyState === 4) {
          if (this.status === 200) {
            // successfully saved
            resolve()
          } else {
            // an error occured
            reject()
          }
        }
      }

      xhttp.open('POST', this.saveUrl, true)
      xhttp.setRequestHeader('X-CSRFToken', this.csrftoken)
      xhttp.setRequestHeader('Content-Type', 'application/json')
      xhttp.send(JSON.stringify({
        mei: this.mei,
        comments: this.comments
      }))
    })
      .then(() => {
        savingModalInstance.el.innerHTML = `
          <div class="modal-content">
            <h4>Saving</h4>
            <p>Saved successfully!</p>
          </div>
          <div class="modal-footer">
            <a href="#!" class="modal-close waves-effect waves-green btn-flat">Close</a>
          </div>
        `
      })
      .catch(() => {
        savingModalInstance.el.innerHTML = `
          <div class="modal-content">
            <h4>Saving</h4>
            <p>An error occured.</p>
          </div>
          <div class="modal-footer">
            <a href="#!" class="modal-close waves-effect waves-green btn-flat">Close</a>
          </div>
        `
      })
  }

  /**
   * Depending on what toolbar button was pressed, update the currentToolMode
   * property on this object.
   *
   * @param {Event} event A DOM event.
   */
  updateCurrentToolMode (event) {
    // if none of the buttons are pressed, abort
    if (event.target.id === 'tools') {
      return
    }

    for (let child of this.tools.children) {
      // find the pressed button
      if (event.target.id === child.id ||
        event.target.parentElement.id === child.id) {
        // make the button look selected
        child.className = 'waves-effect waves-light btn deep-orange darken-3'
        // set the current tool mode to that button
        this.currentToolMode = event.target.id
      } else {
        // make the button look unselected
        child.className = 'waves-effect waves-light btn-flat'
      }
    }
  }
}


/**
 * Makes a GET request, and parses the response as JSON.
 *
 * @param {string} url The URL to request.
 * @return {Promise<Object>} The JSON object retrieved.
 */
const jsonRequest = url =>
  new Promise((resolve, reject) => {
    const xhttp = new XMLHttpRequest()
    xhttp.onreadystatechange = function () {
      if (this.readyState === 4 && this.status === 200) {
        const json = JSON.parse(this.responseText)
        resolve(json)
      }
    }
    xhttp.open('GET', url, true)
    xhttp.send()
  })

/**
 * Gets the value of a cookie with given name.
 *
 * @param {string} name The cookie name whose value we wish to retrieve.
 * @return {string} The cookie value.
 */
const getCookie = name => {
    if (document.cookie && document.cookie !== '') {
      const cookies = document.cookie.split(';')
      const cookie = cookies.find(cookie =>
        cookie.trim().substring(0, name.length + 1) === (name + '='))
      return decodeURIComponent(cookie.trim().substring(name.length + 1))
    }
}
