const INTERSECTION_THRESHOLDS = [0.25];
const ACTIONS = {LIKE: 'like', UNLIKE: 'unlike'};
const STORAGE_KEY = 'likes';

window.addEventListener('load', () => {
  let figures = document.querySelectorAll('article figure');
  let figuresLastIndex = figures.length - 1;
  let umami = window.umami || null;
  let likes = getStoredLikes();

  figures.forEach((figure, index) => {
    let src = figure.dataset.src;
    let isLastFigure = index === figuresLastIndex;
    let img = figure.querySelector('picture img');
    let parents = [img.parentElement, figure];

    // Set data attrs
    img.onload = () => parents.map(el => el.dataset.loaded = 'true');
    parents.map(el => el.dataset.loaded = img.complete + '');
    figure.dataset.liked = likes.has(src) + '';

    // Observe picture visibility
    let observer = new IntersectionObserver(([element, ..._]) => {
      if (!element.isIntersecting) return;
      figure.dataset.visible = 'true';
      observer.unobserve(figure);
      if (isLastFigure && umami) umami.track('page-bottom-viewed', {path: window.location.pathname});
    }, {threshold: INTERSECTION_THRESHOLDS});
    observer.observe(figure);

    // Send tracker events
    if (umami) {
      img.onerror = () => umami.track('image-loading-failed', {src: src});
      figure.addEventListener('click', () => trackPictureLike(src, figure));
    }
  });
});

function getStoredLikes() {
  try {
    let storedValue = localStorage.getItem(STORAGE_KEY) || '[]';
    return new Set(JSON.parse(storedValue));
  } catch (_) {
    return new Set();
  }
}

function trackPictureLike(src, figure) {
  if (figure.dataset.loaded !== 'true') return;
  let action = figure.dataset.liked !== 'true' ? ACTIONS.LIKE : ACTIONS.UNLIKE;
  figure.dataset.liked = (action === ACTIONS.LIKE) + '';
  umami.track(`pic-${action}d`, {src: src});
  storePictureLikeAction(action, src);
}

function storePictureLikeAction(action, src) {
  let likes = getStoredLikes();
  if (action === ACTIONS.LIKE) {
    likes.add(src);
  } else if (action === ACTIONS.UNLIKE) {
    likes.delete(src);
  }
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(Array.from(likes)));
  } catch (e) {
    umami.track('pic-action-failed', {err: e.toString()});
  }
}
