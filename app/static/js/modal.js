function t(source) {
  return (window.I18N || {})[source] || source;
}

const SAFE_URL_SCHEMES = ['http:', 'https:', 'mailto:'];

function isSafeUrl(url) {
  const probe = document.createElement('a');
  probe.href = String(url == null ? '' : url);
  return SAFE_URL_SCHEMES.includes(probe.protocol);
}

function iconAndName(item) {
  const nodes = [];
  if (item.icon && item.icon.class) {
    const icon = document.createElement('i');
    icon.className = item.icon.class;
    nodes.push(icon, document.createTextNode(' '));
  }
  nodes.push(document.createTextNode(item.name == null ? '' : item.name));
  return nodes;
}

function renderMarkdown(content) {
  const escaped = String(content).replace(/</g, '&lt;').replace(/>/g, '&gt;');
  const parsed = new DOMParser().parseFromString(marked.parse(escaped), 'text/html');

  parsed.querySelectorAll('a[href]').forEach((anchor) => {
    if (!SAFE_URL_SCHEMES.includes(anchor.protocol)) {
      anchor.replaceWith(...anchor.childNodes);
    }
  });
  parsed.querySelectorAll('img[src]').forEach((image) => {
    if (!SAFE_URL_SCHEMES.includes(image.protocol)) {
      image.replaceWith(image.alt || '');
    }
  });

  return parsed.body.innerHTML;
}

function openDynamicPopup(subitem) {
  closeAllModals();
  const modalTitle = document.getElementById('dynamicModalLabel');
  modalTitle.replaceChildren(...iconAndName(subitem));

  const identifierBox = document.getElementById('dynamicIdentifierBox');
  const modalContent = document.getElementById('dynamicModalContent');
  if (subitem.identifier) {
    identifierBox.classList.remove('d-none');
    modalContent.value = subitem.identifier;
  } else {
    identifierBox.classList.add('d-none');
    modalContent.value = '';
  }

  function toggleBox(boxId, textId, content) {
    const box = document.getElementById(boxId);
    if (content) {
      box.classList.remove('d-none');
      document.getElementById(textId).innerHTML = renderMarkdown(content);
    } else {
      box.classList.add('d-none');
    }
  }
  
  toggleBox('dynamicModalWarning', 'dynamicModalWarningText', subitem.warning);
  toggleBox('dynamicModalInfo', 'dynamicModalInfoText', subitem.info);

  const descriptionText = document.getElementById('dynamicDescriptionText');
  if (!subitem.url && subitem.description) {
    descriptionText.classList.remove('d-none');
    descriptionText.innerText = subitem.description;
  } else {
    descriptionText.classList.add('d-none');
    descriptionText.innerText = '';
  }

  const linkBox = document.getElementById('dynamicModalLink');
  const linkHref = document.getElementById('dynamicModalLinkHref');
  if (subitem.url) {
    linkBox.classList.remove('d-none');
    linkHref.href = subitem.url;
    if (!isSafeUrl(subitem.url)) {
      linkHref.removeAttribute('href');
    }
    linkHref.innerText = subitem.description || t("Open Link");
    linkHref.classList.remove('iframe');
    linkHref.onclick = null;
    if (subitem.iframe) {
      linkHref.classList.add('iframe');
      linkHref.onclick = function(event) {
        event.preventDefault();
        openIframe(subitem.url);
        closeAllModals();
      };
    }
  } else {
    linkBox.classList.add('d-none');
    linkHref.href = '#';
  }
  function populateSection(sectionId, listId, items, onClickHandler) {
    const section = document.getElementById(sectionId);
    const list = document.getElementById(listId);
    list.innerHTML = '';
  
    if (items && items.length > 0) {
      section.classList.remove('d-none');
      items.forEach(item => {
        const listItem = document.createElement('li');
        listItem.classList.add('list-group-item', 'd-flex', 'justify-content-between', 'align-items-center');
        const label = document.createElement('span');
        label.replaceChildren(...iconAndName(item));
        const button = document.createElement('button');
        button.className = 'btn btn-outline-secondary btn-sm';
        button.textContent = t('Open');
        listItem.replaceChildren(label, button);
        button.addEventListener('click', () => onClickHandler(item));
        list.appendChild(listItem);
      });
    } else {
      section.classList.add('d-none');
    }
  }
  
  populateSection('dynamicAlternativesSection', 'dynamicAlternativesList', subitem.alternatives, openDynamicPopup);
  populateSection('dynamicChildrenSection', 'dynamicChildrenList', subitem.children, openDynamicPopup);  

  const copyButton = document.getElementById('dynamicCopyButton');
  copyButton.onclick = () => {
    modalContent.select();
    navigator.clipboard.writeText(modalContent.value).then(() => {
      alert(t('Identifier copied to clipboard!'));
    });
  };

  const modal = new bootstrap.Modal(document.getElementById('dynamicModal'));
  modal.show();
}

function closeAllModals() {
  const modals = document.querySelectorAll('.modal.show');
  modals.forEach(modal => {
      const modalInstance = bootstrap.Modal.getInstance(modal);
      if (modalInstance) {
          modalInstance.hide();
      }
  });
  const backdrops = document.querySelectorAll('.modal-backdrop');
  backdrops.forEach(backdrop => backdrop.remove());
  document.body.classList.remove('modal-open');
  document.body.style.overflow = '';
  document.body.style.paddingRight = '';
}
