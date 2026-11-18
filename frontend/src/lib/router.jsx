import React, { createContext, useContext, useEffect, useMemo, useState } from 'react';

const RouterContext = createContext({
  location: '/',
  setLocation: () => {},
  params: {},
});

function normalizePath(path) {
  if (!path) return '/';
  const clean = path.split('?')[0].split('#')[0];
  if (clean.length > 1 && clean.endsWith('/')) {
    return clean.slice(0, -1);
  }
  return clean || '/';
}

export function matchPath(pattern, pathname) {
  if (!pattern) return { matched: true, params: {} };
  const normPattern = normalizePath(pattern);
  const normPath = normalizePath(pathname);

  if (normPattern === normPath) {
    return { matched: true, params: {} };
  }

  const patternParts = normPattern.split('/').filter(Boolean);
  const pathParts = normPath.split('/').filter(Boolean);

  if (patternParts.length !== pathParts.length) {
    return { matched: false, params: {} };
  }

  const params = {};
  for (let i = 0; i < patternParts.length; i += 1) {
    const pat = patternParts[i];
    const cur = pathParts[i];
    if (pat.startsWith(':')) {
      params[pat.slice(1)] = decodeURIComponent(cur);
    } else if (pat !== cur) {
      return { matched: false, params: {} };
    }
  }

  return { matched: true, params };
}

export function Router({ children }) {
  const [location, setLocationState] = useState(() => normalizePath(window.location.pathname));

  useEffect(() => {
    const handlePopState = () => {
      setLocationState(normalizePath(window.location.pathname));
    };
    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, []);

  const setLocation = (nextPath, options = {}) => {
    const target = normalizePath(nextPath);
    if (options.replace) {
      window.history.replaceState(null, '', target);
    } else {
      window.history.pushState(null, '', target);
    }
    setLocationState(target);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const value = useMemo(() => ({ location, setLocation, params: {} }), [location]);

  return <RouterContext.Provider value={value}>{children}</RouterContext.Provider>;
}

export function useLocation() {
  const { location, setLocation } = useContext(RouterContext);
  return [location, setLocation];
}

export function useParams() {
  const { params } = useContext(RouterContext);
  return params || {};
}

export function Link({ href, onClick, children, className, ...rest }) {
  const [, setLocation] = useLocation();

  const handleClick = (event) => {
    if (onClick) {
      onClick(event);
    }
    if (
      event.defaultPrevented ||
      event.button !== 0 ||
      event.metaKey ||
      event.altKey ||
      event.ctrlKey ||
      event.shiftKey
    ) {
      return;
    }
    event.preventDefault();
    if (href) {
      setLocation(href);
    }
  };

  return (
    <a href={href || '#'} onClick={handleClick} className={className} {...rest}>
      {children}
    </a>
  );
}

export function Route({ path, component: Component, children }) {
  const { location, setLocation } = useContext(RouterContext);
  const { matched, params } = matchPath(path, location);

  if (!matched) return null;

  return (
    <RouterContext.Provider value={{ location, setLocation, params }}>
      {Component ? <Component params={params} /> : children}
    </RouterContext.Provider>
  );
}

export function Switch({ children }) {
  const { location, setLocation } = useContext(RouterContext);
  const childArray = React.Children.toArray(children);

  for (const child of childArray) {
    if (!React.isValidElement(child)) continue;
    const { path, component: Component, children: routeChildren } = child.props;
    const { matched, params } = matchPath(path, location);
    if (matched) {
      return (
        <RouterContext.Provider value={{ location, setLocation, params }}>
          {Component ? <Component params={params} /> : routeChildren}
        </RouterContext.Provider>
      );
    }
  }

  return null;
}

