window.addEventListener('load', () => {
  document.querySelectorAll('picture img').forEach(img => {
    img.parentElement.dataset.loaded = img.complete ? 'true' : 'false';
    img.onload = () => img.parentElement.dataset.loaded = 'true';
  });

  document.querySelectorAll('article figure').forEach(figure => {
    let observer = new IntersectionObserver(e => {
      if (e[0].isIntersecting) {
        figure.dataset.visible = 'true';
        observer.unobserve(figure);
      }
    }, {threshold: [0.25]});
    observer.observe(figure);
  });
});
