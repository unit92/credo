const toolColors = {
  inspect: "cyan darken-1",
  comment: "cyan darken-1",
  resolve: "cyan darken-1"
}

const groupedElements = [
    'chord', 'beam'
]

/**
 * Wrapper for the functionalities of the Verovio toolkit,
 * tailored to our use case.
 */
class CredoToolkit {
  // class variables
  meiUrl
  commentsUrl
  renderDiv

  mei
  meiDocument // the mei string parsed into an XML document
  comments

  commentModalInstance
  // ID of the thing on which we are commenting
  commentModalId

  resolveModalInstance
  resolveMeasureId // ID of the measure we're resolving
  eliminatedIds // IDs to eliminate

  nameModalInstance

  savingModalInstance

  verovioToolkit

  // toolbar stuff
  tools

  // editing mode
  currentToolMode = 'inspect'

  // Sourced from https://material.io/resources/icons/
  commentSvg = `
    <svg class="tooltipped" data-position="bottom" xmlns="http://www.w3.org/2000/svg" width="480" height="480" viewBox="0 0 24 24">
      <path d="M21.99 4c0-1.1-.89-2-1.99-2H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h14l4 4-.01-18zM18 14H6v-2h12v2zm0-3H6V9h12v2zm0-3H6V6h12v2z" fill="#3f51b5" />
      <path d="M0 0h24v24H0z" fill="transparent"/>
    </svg>
 `

  meiTemplate = `
    <?xml version="1.0" encoding="UTF-8" ?>
    <mei meiversion="3.0.0" xmlns="http://www.music-encoding.org/ns/mei" xmlns:xlink="http://www.w3.org/1999/xlink">
    <music>
      <body>
        <mdiv>
          <score>
            {scoreDef}
            <section>
              {measures}
            </section>
          </score>
        </mdiv>
      </body>
    </music>
    </mei>
  `

  // used for saving revisions
  csrftoken

  /**
   * Constructs the Credo Toolkit.
   *
   * @param {string} meiUrl The URL of the MEI file we wish to render.
   * @param {string} commentsUrl The URL of any associated comments, can be
   * null to indicate no comments.
   * @param {string} resolutionUrl The URL used for merging layers within a measure,
   * can be null to indicate no merge support.
   * @param {string} renderDiv The ID of the div to which we wish to render.
   * @param {string} saveUrl Optional. The URL to POST to when saving revisions.
   */
  constructor (meiUrl, commentsUrl, resolutionUrl, renderDiv, saveUrl) {
    this.meiUrl = meiUrl
    this.commentsUrl = commentsUrl
    this.resolutionUrl = resolutionUrl
    this.renderDiv = renderDiv
    this.saveUrl = saveUrl

    this.verovioToolkit = new verovio.toolkit()

    document.addEventListener('DOMContentLoaded', () => {
      // initialise the comment modal
      const commentModals = document.querySelectorAll('.modal#comment-modal')
      M.Modal.init(commentModals)
      this.commentModalInstance = M.Modal
        .getInstance(document.getElementById('comment-modal'))

      // initialise the resolve modal
      const resolveModals = document.querySelectorAll('.modal#resolve-modal')
      M.Modal.init(resolveModals, {
        onCloseEnd: this.clearResolveModal
      })
      this.resolveModalInstance = M.Modal
        .getInstance(document.getElementById('resolve-modal'))
      document.getElementById('resolveDiv')
        .addEventListener('click', this.resolveNote.bind(this))

      const makeRevisionButton = document.querySelector('button#makeRevisionButton')
      if (makeRevisionButton) {
        const nameModals = document.querySelectorAll('.modal#name-modal')
        M.Modal.init(nameModals)
        this.nameModalInstance = M.Modal
          .getInstance(document.getElementById('name-modal'))
        makeRevisionButton.addEventListener('click', this.openNameModal.bind(this))
      }

      const nameModalSubmit = document.getElementById('name-modal-submit')
      if (nameModalSubmit) {
        nameModalSubmit.addEventListener('click', function() {
          const makeRevisionButton = document.querySelector('button#makeRevisionButton')
          const revisionNameInput = document.querySelector('input#revision-name-input')
          window.location.href = makeRevisionButton.getAttribute('target') + '&name=' + encodeURI(revisionNameInput.value)
        })
      }

      const nameModalClose = document.getElementById('name-modal-close')
      if (nameModalClose) {
        nameModalClose.addEventListener('click', this.clearNameModal.bind(this))
      }
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

    const resolveModalSubmit = document.getElementById('resolve-modal-submit')
    if (resolveModalSubmit) {
      resolveModalSubmit.addEventListener('click', this.submitMeasureResolution.bind(this))
    }

    const resolveModalCancel = document.getElementById('resolve-modal-cancel')
    if (resolveModalCancel) {
      resolveModalCancel.addEventListener('click', this.cancelMeasureResolution.bind(this))
    }

    const resolvePlayButton = document.getElementById('resolve-play')
    if (resolvePlayButton) {
      resolvePlayButton.addEventListener(
        'click',
        this.playSnippet.bind(this)
      )
    }
    const resolveSwapLayersButton = document.getElementById('resolve-swap-layers')
    if (resolveSwapLayersButton) {
      resolveSwapLayersButton.addEventListener(
        'click',
        this.swapResolutionLayers.bind(this)
      )
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
    } else if (this.currentToolMode === 'resolve') {
      this.resolveEventListener(event)
    }
  }

  openNameModal (event) {
    this.nameModalInstance.open()
  }

  clearNameModal (event) {
    this.nameModalInstance.close()
  }

  /**
   * Reacts to the click event by reacting as if in resolve mode.
   *
   * @param {Event} event A HTML DOM event.
   */
  resolveEventListener (event) {
    // get the event target
    let target = event.target

    // keep going upwards until we find an element with className 'measure'
    // or the target is no longer truthy
    while (target && !Array.from(target.classList).includes('measure')) {
      target = target.parentElement
    }

    // if the target is null, we didn't match a measure, return
    if (!target) {
      return
    }

    this.openResolveModal(target.id)
  }

  /**
   * Opens up the resolve modal for a given measure.
   *
   * @param {string} targetId The ID of the measure to resolve.
   */
  openResolveModal (targetId) {
    this.eliminatedIds = []

    const meiMeasure = this.meiDocument.evaluate(
      `//mei:measure[@xml:id="${targetId}"]`,
      this.meiDocument,
      this.namespaceResolver,
      XPathResult.ANY_TYPE,
      null
    ).iterateNext()

    const resolveMeiString = this.generateResolveMei(meiMeasure)

    const resolveDiv = document.getElementById('resolveDiv')
    resolveDiv.innerHTML = this.verovioToolkit.renderData(
      resolveMeiString,
      {
        svgViewBox: true,
        adjustPageHeight: true
      }
    )

    const outerSvgElement = resolveDiv.children[0]
    const innerSvgElement = outerSvgElement.querySelector('.definition-scale')
    const marginElement = innerSvgElement.querySelector('.page-margin')
    const measureElement = innerSvgElement.querySelector('.measure')

    // I am painfully aware of how much of a hack the following is, but Verovio was
    //  too inflexible to allow me to center and scale the measure onto the resolve modal.
    setTimeout(() => {
        const marginBBox = marginElement.getBBox()
        innerSvgElement.setAttribute(
          'viewBox',
          `0 0 ${marginBBox.width} ${marginBBox.height + 200}`
        )
        resolveDiv.appendChild(innerSvgElement)
        outerSvgElement.remove()
        marginElement.setAttribute('transform', `translate(${measureElement.getBBox().x*-1},50)`)
        // marginElement.setAttribute('transform', '')
        // outerSvgElement.setAttribute(
          // 'viewBox',
          // `0 0 ${marginBBox.width / 9} ${marginBBox.height / 9}`
        // )
    }, 20)


    this.resolveMeasureId = targetId
    this.resolveModalInstance.open()
  }

  /**
   * Attempts to resolve the notation clicked upon.
   *
   * @param {Event} The HTML DOM event.
   */
  resolveNote (event) {
    let target = event.target
    const lowAlpha = 0.5
    while (target && !target.id.match(/m-[0-9]*/)) {
      target = target.parentElement
    }

    // Don't affect the note if it's not coloured
    if (!target) {
      return
    }

    // If target is part of a group e.g. chord, beam, then toggle visibility for the group
    const meiTarget = this.meiDocument.evaluate(
      `//*[@xml:id="${target.id}"]`,
      this.meiDocument,
      this.namespaceResolver,
      XPathResult.ANY_TYPE,
      null
    ).iterateNext()

    let meiGroupTarget = null
    groupedElements.forEach(group_tag => {
      const result = this.meiDocument.evaluate(
        `ancestor-or-self::mei:${group_tag}`,
        meiTarget,
        this.namespaceResolver,
        XPathResult.ANY_TYPE,
        null
      ).iterateNext()
      if (result) {
        meiGroupTarget = result
      }
    })

    let targets = [target]
    if (meiGroupTarget) {
      // Find ID of group target
      const meiGroupTargetId = this.meiDocument.evaluate(
        `@xml:id`,
        meiGroupTarget,
        this.namespaceResolver,
        XPathResult.ANY_TYPE,
        null
      ).iterateNext()

      let svgGroupTarget = target

      // Search SVG for group target ID
      while (svgGroupTarget && svgGroupTarget.id !== meiGroupTargetId.value) {
        svgGroupTarget = svgGroupTarget.parentElement
      }

      // Update visibility for all sub elements
      targets = [svgGroupTarget]
      targets.push.apply(targets, svgGroupTarget.querySelectorAll('g'))
      targets = targets.filter(elem => elem.className.baseVal !== 'stem')
    }

    targets.forEach(target => {

      const eliminated = target.getAttribute('eliminated')
      let fillAttribute = target.getAttribute('fill') || target.parentElement.getAttribute('fill')
      if (!fillAttribute) {
        return
      }

      if (eliminated === null || eliminated === 'false') {
        target.setAttribute('eliminated', 'true')
        // Add transparency and add to list of IDs to eliminate
        if (fillAttribute.startsWith('hsl(')) {
          fillAttribute = fillAttribute.replace('hsl', 'hsla')
        }
        fillAttribute = fillAttribute.replace(')', `, ${lowAlpha})`)
        if (!this.eliminatedIds.includes(target.id)) {
          this.eliminatedIds.push(target.id)
        }
      } else {
        target.setAttribute('eliminated', 'false')
        // remove transparency and remove from list of IDs to eliminate
        if (fillAttribute.startsWith('hsla(')) {
          fillAttribute = fillAttribute.replace('hsla', 'hsl')
        }
        fillAttribute = fillAttribute.replace(/, [0-9\.]*\)/, ')')
        this.eliminatedIds = this.eliminatedIds.filter(
          id => id !== target.id
        )
      }

      target.setAttribute('fill', fillAttribute)
    })
  }

  /**
   * Propagates the changes to the measure to the full piece.
   */
  submitMeasureResolution () {

    const resolveDiv = document.getElementById('resolveDiv')

    const meiMeasure = this.meiDocument.evaluate(
      `//mei:measure[@xml:id="${this.resolveMeasureId}"]`,
      this.meiDocument,
      this.namespaceResolver,
      XPathResult.ANY_TYPE,
      null
    ).iterateNext()

    const measureString = meiMeasure.outerHTML
    let measureCopy = new DOMParser().parseFromString(measureString, 'text/xml')

    // Search for nodes to eliminate from the measure
    const notationXPath = measureCopy.evaluate(
      `//*[@xml:id]`,
      measureCopy,
      this.namespaceResolver,
      XPathResult.ANY_TYPE,
      null
    )

    // Maintain an array to remove, since we can't remove while iterating
    let notation = notationXPath.iterateNext()
    const toRemove = []
    while (notation) {
      if (this.eliminatedIds.includes(notation.getAttribute('xml:id'))) {
        toRemove.push(notation)
      }
      notation = notationXPath.iterateNext()
    }

    // Remove nodes from measure
    toRemove.forEach(element => {
      element.setAttribute('visible', 'false')
    })

    const body = {
      'content': {
        'mei': {
          'detail': btoa(new XMLSerializer().serializeToString(measureCopy)),
          'encoding': 'base64'
        }
      }
    }
    
    // Merge the measure layers on the server and reinject into the meiDocument
    return new Promise((resolve, reject) => {
      const xhttp = new XMLHttpRequest()
      xhttp.onreadystatechange = function () {
        if (this.readyState === 4) {
          if (this.status === 200) {
            const json = JSON.parse(this.responseText)
            resolve(json)
          } else {
            reject()
          }
        }
      }

      xhttp.open('POST', this.resolutionUrl, true)
      xhttp.setRequestHeader('X-CSRFToken', this.csrftoken)
      xhttp.setRequestHeader('Content-Type', 'application/json')
      xhttp.send(JSON.stringify(body))
    }).then(json => {
      if (json.content.resolved === 'true') {
        // Decode from base 64
        const resolvedMeasureString = atob(json.content.mei.detail)

        // Remove colour from any remaining notes
        const resolvedMeasure = new DOMParser().parseFromString(resolvedMeasureString, 'text/xml')
        const colouredNotation = Array.from(resolvedMeasure.querySelectorAll('[color]'))
        colouredNotation.forEach(notation => {
          notation.removeAttribute('color')
        })

        // Update measure on meiDocument
        meiMeasure.outerHTML = new XMLSerializer().serializeToString(resolvedMeasure)

        // Update the mei string and rerender
        this.mei = new XMLSerializer().serializeToString(this.meiDocument)
        this.renderMei()

        // close the modal
        this.resolveModalInstance.close()
        const feedbackDiv = document.querySelector('#resolveError')
        feedbackDiv.textContent = ''
      } else {
        const feedbackDiv = document.querySelector('#resolveError')
        feedbackDiv.textContent = 'Some notes are still in conflict. Click on notes to toggle selection.'
      }
    })
  }

  cancelMeasureResolution() {
    const feedbackDiv = document.querySelector('#resolveError')
    feedbackDiv.textContent = ''
  }

  /**
   * Converts the snippet open in the resolve tool into MIDI and plays it
   */
  playSnippet () {
    const song = 'data:audio/midi;base64,' + this.verovioToolkit.renderToMIDI()
    $('#player').midiPlayer.play(song)
  }

  /**
   * Swaps the order in which the diff layers are rendered for the resolution.
   */
  swapResolutionLayers () {
    // a dictionary keyed by colours used in the layer
    const colourLayers = {}

    const colouredNotation = Array.from(
      document.querySelectorAll('#resolveDiv [fill]'))

    colouredNotation.forEach(notation => {
      // get the colour, and the layer of this notation
      const colour = notation.getAttribute('fill')

      // keep going upward until we're at a layer
      let currentElement = notation
      while (!Array.from(currentElement.classList).includes('layer')) {
        if (!currentElement) {
          return
        }
        currentElement = currentElement.parentElement
      }

      // add the colour and layer to the object tracking colours and layers
      if (!colourLayers[colour]) {
        colourLayers[colour] = [currentElement]
      } else {
        if (!colourLayers[colour].includes(currentElement)) {
          colourLayers[colour].push(currentElement)
        }
      }
    })

    // reappend the children in the correct order
    Object.values(colourLayers).reverse().forEach(colourLayerSet => {
      colourLayerSet.forEach(layer => {
        layer.parentElement.appendChild(layer)
      })
    })
  }

  /**
   * Clears the resolve modal.
   */
  clearResolveModal () {
    document.getElementById('resolveDiv').innerHTML = ''
  }

  /**
   * Generates the MEI to display in the resolve modal.
   *
   * @param {Node} measure The measure to render.
   * @return {string} The generated MEI as a string.
   */
  generateResolveMei (measure) {
    let mei = this.meiTemplate
    mei = mei.replace(
      '{scoreDef}',
      this.meiDocument.querySelector('scoreDef').outerHTML)
    mei = mei.replace('{measures}', measure.outerHTML)

    return mei
  }

  /**
   * Namespace resolver for parsing MEI Document.
   *
   * @param {string} prefix The namespace prefix.
   * @return {string} The resolved namespace.
   */
  namespaceResolver (prefix) {
    const namespaces = {
      'xml': 'http://www.w3.org/XML/1998/namespace',
      'mei': 'http://www.music-encoding.org/ns/mei',
      'xlink': 'http://www.w3.org/1999/xlink'
    }

    return namespaces[prefix] || null
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
      .then(json => {
        if (json.content.mei) {
          return atob(json.content.mei.detail)
        } else if (json.content.diff) {
          return atob(json.content.diff.detail)
        }
      })
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
        this.meiDocument = new DOMParser().parseFromString(mei, 'text/xml')
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
   * Goes over a rendered SVG in the renderDiv, and proceeds to make notation
   * more easily clickable.
   */
  improveClickHitboxes () {
    // get all clickable notation
    // the ID parameter matches IDs starting with the given term
    const interactables = document.querySelectorAll('#renderDiv [id^="m-"]')

    for (let interactable of interactables) {
      // add this property to each, to make mouse events use the bounding box
      interactable.setAttribute('pointer-events', 'bounding-box')
    }
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

    // post-verovio render, modify the SVG to have better click hitboxes
    this.improveClickHitboxes()

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

    // re-add box-shadow
    renderElement.classList.remove("loading")
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
    commentElement.setAttribute('data-tooltip', escapeHtmlCharacters(text))
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

    commentElement.setAttribute('data-tooltip', escapeHtmlCharacters(text))

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
        child.className = 'waves-effect waves-light btn ' + toolColors[child.id]
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
        cookie ? cookie.trim().substring(0, name.length + 1) === (name + '=') : null
      )
      return cookie ? decodeURIComponent(cookie.trim().substring(name.length + 1)) : null
    }
}

/**
 * Takes in a string and escapes HTML characters.
 *
 * @param {string} test The text to escape.
 * @return {string} The escaped text.
 */
escapeHtmlCharacters = text => text
  .replace(/&/g, '&amp;')
  .replace(/</g, '&lt;')
  .replace(/>/g, '&gt;')
  .replace(/"/g, '&quot;')
  .replace(/'/g, '&#039;')

// vim: shiftwidth=2
