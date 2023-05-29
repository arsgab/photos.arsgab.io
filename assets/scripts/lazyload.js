const INTERSECTION_THRESHOLDS = [0.25];

window.addEventListener('load', () => {
  let figures = document.querySelectorAll('article figure');
  let figuresLastIndex = figures.length - 1;
  let umami = window.umami || null;

  figures.forEach((figure, index) => {
    let isLastFigure = index === figuresLastIndex;
    let img = figure.querySelector('picture img');
    img.parentElement.dataset.loaded = img.complete ? 'true' : 'false';
    img.onload = () => img.parentElement.dataset.loaded = 'true';
    let observer = new IntersectionObserver(([element, ..._]) => {
      if (!element.isIntersecting) return false;
      figure.dataset.visible = 'true';
      observer.unobserve(figure);
      if (isLastFigure && umami) umami.track('page-bottom-viewed', {path: window.location.pathname});
    }, {threshold: INTERSECTION_THRESHOLDS});
    observer.observe(figure);

    // Send tracker event if image was not loaded
    if (umami) {
      img.onerror = () => umami.track('image-loading-failed', {img: figure.dataset.src || ''});
    }
  });
});
