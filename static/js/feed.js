document.addEventListener('DOMContentLoaded', function() {
  console.log('DOM loaded, feedData exists:', !!window.feedData);

  if (!window.feedData) {
    console.error('No feedData found!');
    return;
  }

  // Parse JSON string if needed
  let feedItems = window.feedData;
  if (typeof feedItems === 'string') {
    try {
      feedItems = JSON.parse(feedItems);
    } catch (e) {
      console.error('Failed to parse feedData JSON:', e);
      return;
    }
  }

  console.log('Parsed feedItems:', feedItems);
  console.log('feedItems is array:', Array.isArray(feedItems));

  const pageSize = 10;
  const totalItems = feedItems.length;
  const totalPages = Math.ceil(totalItems / pageSize);

  console.log('pageSize:', pageSize, 'totalItems:', totalItems, 'totalPages:', totalPages);

  // Get current page from URL
  const urlParams = new URLSearchParams(window.location.search);
  let currentPage = parseInt(urlParams.get('page')) || 1;
  if (currentPage < 1) currentPage = 1;
  if (currentPage > totalPages) currentPage = totalPages;

  function renderItems(page) {
    const startIndex = (page - 1) * pageSize;
    const endIndex = Math.min(startIndex + pageSize, totalItems);
    const pageItems = feedItems.slice(startIndex, endIndex);

    const itemsContainer = document.getElementById('feed-items');
    itemsContainer.innerHTML = '';

    pageItems.forEach(item => {
      const article = document.createElement('article');
      article.className = 'content-item';

      let metaHtml = '';
      if (item.published) {
        const date = new Date(item.published).toISOString().split('T')[0];
        metaHtml += `<time>${date}</time>`;
      }
      if (item.source) {
        metaHtml += `<span class="source">${item.source}</span>`;
      }

      article.innerHTML = `
        <div class="content-item-content">
          ${item.image ? `<div class="content-item-image">
            <img src="${item.image}" alt="${item.title}" loading="lazy">
          </div>` : ''}
          <div class="content-item-text">
            <h2><a href="${item.link}" target="_blank" rel="noopener">${item.title}</a></h2>
            <div class="content-item-meta">${metaHtml}</div>
            ${item.summary ? `<p class="content-summary">${item.summary}</p>` : ''}
          </div>
        </div>
      `;

      itemsContainer.appendChild(article);
    });

    // Update meta text
    const metaText = document.getElementById('feed-meta-text');
    const generatedDate = new Date(window.feedGeneratedAt).toLocaleString();
    metaText.textContent = `Showing ${startIndex + 1}-${endIndex} of ${totalItems} items • Last updated: ${generatedDate}`;

    // Update pagination
    updatePagination(page);
  }

  function updatePagination(page) {
    const pagination = document.getElementById('pagination');
    const prevBtn = document.getElementById('prev-btn');
    const nextBtn = document.getElementById('next-btn');
    const pageInfo = document.getElementById('page-info');

    if (totalPages <= 1) {
      pagination.style.display = 'none';
      return;
    }

    pagination.style.display = 'flex';
    pageInfo.textContent = `Page ${page} of ${totalPages}`;

    // Previous button
    if (page <= 1) {
      prevBtn.style.opacity = '0.5';
      prevBtn.style.pointerEvents = 'none';
    } else {
      prevBtn.style.opacity = '1';
      prevBtn.style.pointerEvents = 'auto';
      prevBtn.onclick = () => goToPage(page - 1);
    }

    // Next button
    if (page >= totalPages) {
      nextBtn.style.opacity = '0.5';
      nextBtn.style.pointerEvents = 'none';
    } else {
      nextBtn.style.opacity = '1';
      nextBtn.style.pointerEvents = 'auto';
      nextBtn.onclick = () => goToPage(page + 1);
    }
  }

  function goToPage(page) {
    const url = new URL(window.location);
    if (page === 1) {
      url.searchParams.delete('page');
    } else {
      url.searchParams.set('page', page);
    }
    window.history.pushState({}, '', url);
    currentPage = page;
    renderItems(page);
  }

  // Handle browser back/forward
  window.addEventListener('popstate', function() {
    const urlParams = new URLSearchParams(window.location.search);
    const page = parseInt(urlParams.get('page')) || 1;
    currentPage = page;
    renderItems(page);
  });

  // Initial render
  renderItems(currentPage);
});