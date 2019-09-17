/**
 * This file exists to neatly wrap around any rendering complexities from
 * Verovio. Any HTML that uses this script will also need to use the Verovio
 * Toolkit.
 */

/**
 * This is an object of element IDs and their corresponding toolkits. Toolkits
 * maintain information on the currently loaded MEI file that we may want to use
 * later, so we will maintain different toolkits for different renders.
 */
const verovioToolkits = {}

/**
 * Gets the toolkit if it exists for this rendering element, otherwise generates
 * and returns one.
 *
 * @param {string} id The id of the rendering element in the DOM.
 * @return The Verovio Toolkit for that element in the DOM.
 */
getToolkit = id => {
  if (!verovioToolkits[id]) {
    verovioToolkits[id] = new verovio.toolkit()
  }
  return verovioToolkits[id]
}

/**
 * Renders the given MEI file (currently from URL) to an inline SVG to be
 * contained in an element by the given ID.
 *
 * @param {string} url The URL of the MEI file.
 * @param {string} id The element ID into which we insert the rendered image.
 */
renderMei = (url, id) => {
  const toolkit = getToolkit(id)

  const xhttp = new XMLHttpRequest()
  xhttp.onreadystatechange = function () {
    if (this.readyState === 4 && this.status === 200) {
      // store the data on the toolkit
      toolkit.loadData(data)
      console.log(url.split('/')[1])
      if (url.split('/')[1] === 'mei') {
        // TODO Update /mei endpoint to be more like the diff endpoint with b64 encoding
        const renderDiv = document.getElementById(id)
        renderDiv.innerHTML = toolkit.renderData(this.responseText, {svgViewBox: true})
      } else {
        meiJson = JSON.parse(this.responseText)
        const childDivs = document.querySelectorAll(`#${id} > div`)
        if (childDivs.length === meiJson['content']['sources'].length + 1) {
          for (let i = 0; i < childDivs.length; ++i) {
            if (i === 0) {
              diff = atob(meiJson['content']['diff']['details'])
              childDivs[i].innerHTML = toolkit.renderData(diff, {svgViewBox: true})
            } else {
              source = atob(meiJson['content']['sources'][i-1]['details'])
              childDivs[i].innerHTML = toolkit.renderData(source, {svgViewBox: true})
            }
          }
        }
      }
      
    }
  }
  xhttp.open('GET', url, true)
  xhttp.send()
}
