const INTERSECTION_THRESHOLDS = [0.25];

window.addEventListener('load', () => {
  const umami = window.umami || null;
  const figures = document.querySelectorAll('article figure');
  const figuresLastIndex = figures.length - 1;

  document.querySelectorAll('picture img').forEach(img => {
    img.parentElement.dataset.loaded = img.complete ? 'true' : 'false';
    img.onload = () => img.parentElement.dataset.loaded = 'true';
  });

  figures.forEach((figure, index) => {
    let isLastFigure = index === figuresLastIndex;
    let observer = new IntersectionObserver(([element, ..._]) => {
      if (!element.isIntersecting) return false;
      figure.dataset.visible = 'true';
      observer.unobserve(figure);
      if (isLastFigure && umami) umami.trackEvent('page-bottom-viewed', {path: window.location.pathname});
    }, {threshold: INTERSECTION_THRESHOLDS});
    observer.observe(figure);
  });
});
