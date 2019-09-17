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

  verovioToolkit

  // Sourced from https://material.io/resources/icons/
  commentSvg = `
    <svg class="tooltipped" data-position="bottom" xmlns="http://www.w3.org/2000/svg" width="480" height="480" viewBox="0 0 24 24">
      <path d="M21.99 4c0-1.1-.89-2-1.99-2H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h14l4 4-.01-18zM18 14H6v-2h12v2zm0-3H6V9h12v2zm0-3H6V6h12v2z" fill="green" />
      <path d="M0 0h24v24H0z" fill="transparent"/>
    </svg>
 `

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
    this.comments.forEach(this.renderComment.bind(this))

    // render the tooltip showing the comment text
    M.Tooltip.init(document.querySelectorAll('.tooltipped', undefined))
  }

  renderComment (comment) {
    // get the element to which we want to attack the comment
    const element = document.getElementById(comment.position)
    const position = element.getBBox()

    element.innerHTML += this.commentSvg

    // get the SVG for the comment
    const commentElement = element.children[(element.children.length - 1)]
    commentElement.setAttribute('x', position.x)
    commentElement.setAttribute('y', position.y)

    // set the comment text
    commentElement.setAttribute('data-tooltip', comment.text)
  }
}
