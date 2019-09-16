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
      // TODO
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

  }

  renderComment (comment) {

  }
}
