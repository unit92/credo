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

  verovioToolkit

  // Sourced from https://material.io/resources/icons/
  commentSvg = `
    <svg class="tooltipped" data-position="bottom" xmlns="http://www.w3.org/2000/svg" width="480" height="480" viewBox="0 0 24 24">
      <path d="M21.99 4c0-1.1-.89-2-1.99-2H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h14l4 4-.01-18zM18 14H6v-2h12v2zm0-3H6V9h12v2zm0-3H6V6h12v2z" fill="green" />
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
   */
  constructor (meiUrl, commentsUrl, renderDiv) {
    this.meiUrl = meiUrl
    this.commentsUrl = commentsUrl
    this.renderDiv = renderDiv

    this.verovioToolkit = new verovio.toolkit()

    // initialise modal
    document.addEventListener('DOMContentLoaded', () => {
      const modals = document.querySelectorAll('.modal')
      M.Modal.init(modals)
      this.commentModalInstance = M.Modal
        .getInstance(document.getElementById('comment-modal'))
    })
    
    // attach the note grabbing listener to the event div
    document.getElementById(renderDiv)
      .addEventListener('click', this.commmentEventListener.bind(this))

    // attach a comment submitting method to the submit button in the modal
    document.getElementById('comment-modal-submit')
      .addEventListener('click', this.updateCommentFromModal.bind(this))

    // get the CSRF token
    this.csrftoken = getCookie('csrftoken')
  }

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

    this.comments[this.commentModalId] = document
      .getElementById('comment-modal-text').value

    if (alreadyExisting) {
      this.updateComment(
        this.commentModalId,
        this.comments[this.commentModalId]
      )
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
    return new Promise((resolve, reject) => {
      const xhttp = new XMLHttpRequest()
      xhttp.onreadystatechange = function () {
        if (this.readyState === 4 && this.status === 200) {
          resolve(this.responseText)
        }
      }
      xhttp.open('GET', this.meiUrl, true)
      xhttp.send()
    })
  }

  /**
   * Loads the MEI, and saves it to the class and the Verovio toolkit.
   *
   * @return {Promise<void>} A promise to resolve upon completion.
   */
  loadAndSaveMei () {
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
    return new Promise((resolve, reject) => {
      const xhttp = new XMLHttpRequest()
      xhttp.onreadystatechange = function () {
        if (this.readyState === 4 && this.status === 200) {
          resolve(this.responseText)
        }
      }
      xhttp.open('GET', this.commentsUrl, true)
      xhttp.send()
    })
  }

  /**
   * Loads the comments, and saves them to the class.
   *
   * @return {Promise<void>} A promise to resolve upon completion.
   */
  loadAndSaveComments () {
    return this.loadComments()
      .then(comments => this.comments = JSON.parse(comments))
  }

  /**
   * Renders the MEI file, and any comments associated.
   */
  async render () {
    // load the MEI if it hasn't been loaded yet
    if (!this.mei) {
      await this.loadAndSaveMei()
    }

    // render the MEI
    this.renderMei()

    if (this.commentsUrl) {
      // if there are comments, load the comments
      if (!this.comments) {
        await this.loadAndSaveComments()
      }

      this.renderComments()
    } else {
      this.comments = {}
    }
  }

  /**
   * Renders the given MEI to an inline SVG to be contained in the element
   * specified at construction.
   */
  renderMei () {
    const renderElement = document.getElementById(this.renderDiv)
    renderElement.innerHTML = this.verovioToolkit.renderData(
          this.responseText,
          {svgViewBox: true}
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
    commentElement.setAttribute('x', position.x)
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
    if (text) {
      this.comments[elementId] = text
    } else {
      // delete if being removed
      delete this.comments[elementId]
    }

    // get the element
    const element = document.getElementById(elementId)

    // get the comment on the element
    const commentElement = element.children[(element.children.length - 1)]

    // set the comment text or remove if no text
    if (text) {
      commentElement.setAttribute('data-tooltip', text)
    } else {
      commentElement.remove()
    }

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
      let xPosition = position.x - tooltipElement.getBoundingClientRect().width / 2 + commentIcon.getBoundingClientRect().width / 2
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
   * Save revision by making a POST request to the server, and then redirect to
   * the saved revision.
   */
  saveRevision () {
    const mei = this.mei
    const comments = this.comments

    const request = new Promise((resolve, reject) => {
      const xhttp = new XMLHttpRequest()
      xhttp.onreadystatechange = function () {
        if (this.readyState === 4 && this.status === 200) {
          resolve(this.responseText)
        }
      }

      xhttp.open('POST', '../revisions/', true)
      xhttp.setRequestHeader('Content-Type', 'application/json;charset=UTF-8')
      xhttp.setRequestHeader('X-CSRFToken', this.csrftoken)
      xhttp.send(JSON.stringify({
        mei,
        comments,
      }))
    })
      .then(responseText => {
        window.location.replace(responseText)
      })
  }
}

const getCookie = name => {
    if (document.cookie && document.cookie !== '') {
      const cookies = document.cookie.split(';')
      const cookie = cookies.find(cookie =>
        cookie.trim().substring(0, name.length + 1) === (name + '='))
      return decodeURIComponent(cookie.trim().substring(name.length + 1))
    }
}
