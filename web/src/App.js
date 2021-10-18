import { createTheme } from '@material-ui/core/styles';
import { useState } from 'react';
import './App.css';
import { BrowserRouter, Route } from 'react-router-dom';
import NorthStarThemeProvider from 'aws-northstar/components/NorthStarThemeProvider';
import AppLayout from 'aws-northstar/layouts/AppLayout';
import Header from 'aws-northstar/components/Header';
import Select from 'aws-northstar/components/Select';
import { getTheme } from 'aws-northstar/themes/default';
import SideNavigation, { SideNavigationItemType } from 'aws-northstar/components/SideNavigation';

import { MainContext, PosContext } from './components/Context';
import { floor } from './data';
import Inline from 'aws-northstar/layouts/Inline';
import * as Routes from './Routes';
import Amplify from 'aws-amplify';
import awsmobile from './aws-exports';

Amplify.configure(awsmobile);

function App() {
  const theme = createTheme({
    ...getTheme(),
    palette: {
      primary: {
        main: '#232F3E',
      },
    },
  });

  //Context
  const [context, setContext] = useState({
    office: 'DEMO',
    floor: '10F',
  });

  const [position, setPosition] = useState([{ pos: [0, 0], SortKey: null }]);

  const officeOptions = [
    {
      label: 'Tokyo',
      options: [{ label: 'DEMO', value: 'DEMO' }],
    },
  ];

  const navigationItems = [
    { type: SideNavigationItemType.LINK, text: 'Floormap', href: '/' },
    { type: SideNavigationItemType.LINK, text: 'Portfolio', href: '/portfolio' },
    { type: SideNavigationItemType.DIVIDER },
    {
      type: SideNavigationItemType.LINK,
      text: 'Blog about AWS Office Lens',
      href: 'https://docs.yoursite.com',
    },
  ];
  const navigation = (
    <SideNavigation
      header={{
        href: '/',
        text: 'AWS Office Lens',
      }}
      items={navigationItems}
    />
  );

  const onChangeOffice = (event) => {
    if (typeof event.target.value !== 'undefined') {
      setContext((prevctx) => ({
        ...prevctx,
        office: event.target.value,
        floor: floor[event.target.value][0].value,
        zoom: context.defaultZoom,
        center: [0, 0],
        target: null,
      }));
    }
  };

  const rightContent = (
    <Inline>
      <Select options={officeOptions} selectedOption={{ value: context.office }} onChange={onChangeOffice} />
    </Inline>
  );
  return (
    <BrowserRouter>
      <NorthStarThemeProvider theme={theme}>
        <MainContext.Provider value={[context, setContext]}>
          <PosContext.Provider value={[position, setPosition]}>
              <AppLayout
                header={<Header logoPath="./logo-aws.png" rightContent={rightContent} />}
                navigation={navigation}
              >
                <Route exact path="/" component={Routes.Floormap} />
                <Route exact path="/portfolio" component={Routes.Portfolio} />
              </AppLayout>
          </PosContext.Provider>
        </MainContext.Provider>
      </NorthStarThemeProvider>
    </BrowserRouter>
  );
}

export default App;
