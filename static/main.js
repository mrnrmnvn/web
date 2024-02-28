
const STORAGE_DISPLAYED_TEXT_KEY = 'displayed_text'

document.addEventListener("DOMContentLoaded", () => {
    const currently_displayed_text = document.querySelector('#currently_displayed_text')
    const tags = document.querySelectorAll(".btn-tag");
    const updateBtn = document.getElementById('update');

    const storageText = localStorage.getItem(STORAGE_DISPLAYED_TEXT_KEY)

    if (storageText) currently_displayed_text.innerHTML = storageText;

    let buttonPressedBackground ="#ffffff";

    updateBtn.addEventListener('click', (e) => {
        localStorage.removeItem(STORAGE_DISPLAYED_TEXT_KEY)
    })

    tags.forEach(tag => tag.addEventListener('click', (e) => {
        const background = e.target.style.background

        const ss = document.styleSheets[0]
        ss.deleteRule(0)
        ss.insertRule(`*::selection { background: ${background} }`, 0)
        buttonPressedBackground = background
    }))

    currently_displayed_text.addEventListener('mouseup', (event) => {
        const s = window.getSelection();

        const text = currently_displayed_text.innerHTML.trim();

        console.log(text)
        const selectionText = s.getRangeAt(0).cloneContents().textContent

        const result = text.replace(selectionText, `<span style="background:${buttonPressedBackground}">${selectionText}</span>`)
        currently_displayed_text.innerHTML = result

        localStorage.setItem(STORAGE_DISPLAYED_TEXT_KEY, result)
        

    })

})