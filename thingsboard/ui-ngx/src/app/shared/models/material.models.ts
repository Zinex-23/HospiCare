///
/// Copyright © 2016-2025 The Thingsboard Authors
///
/// Licensed under the Apache License, Version 2.0 (the "License");
/// you may not use this file except in compliance with the License.
/// You may obtain a copy of the License at
///
///     http://www.apache.org/licenses/LICENSE-2.0
///
/// Unless required by applicable law or agreed to in writing, software
/// distributed under the License is distributed on an "AS IS" BASIS,
/// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
/// See the License for the specific language governing permissions and
/// limitations under the License.
///

import tinycolor from 'tinycolor2';

export interface MaterialColorItem {
  value: string;
  group: string;
  label: string;
  isDark: boolean;
}

export const materialColorPalette: {[palette: string]: {[spectrum: string]: string}} = {
  red: {
    50: '#ffebee',
    100: '#ffcdd2',
    200: '#ef9a9a',
    300: '#e57373',
    400: '#ef5350',
    500: '#f44336',
    600: '#e53935',
    700: '#d32f2f',
    800: '#c62828',
    900: '#b71c1c',
    A100: '#ff8a80',
    A200: '#ff5252',
    A400: '#ff1744',
    A700: '#d50000'
  },
  pink: {
    50: '#fce4ec',
    100: '#f8bbd0',
    200: '#f48fb1',
    300: '#f06292',
    400: '#ec407a',
    500: '#e91e63',
    600: '#d81b60',
    700: '#c2185b',
    800: '#ad1457',
    900: '#880e4f',
    A100: '#ff80ab',
    A200: '#ff4081',
    A400: '#f50057',
    A700: '#c51162'
  },
  purple: {
    50: '#f3e5f5',
    100: '#e1bee7',
    200: '#ce93d8',
    300: '#ba68c8',
    400: '#ab47bc',
    500: '#9c27b0',
    600: '#8e24aa',
    700: '#7b1fa2',
    800: '#1B9A2E',
    900: '#148C20',
    A100: '#ea80fc',
    A200: '#e040fb',
    A400: '#d500f9',
    A700: '#00FF2A'
  },
  'deep-purple': {
    50: '#ede7f6',
    100: '#d1c4e9',
    200: '#9DDBA1',
    300: '#75CD7B',
    400: '#57C25F',
    500: '#3AB743',
    600: '#35B13C',
    700: '#2DA833',
    800: '#27A02B',
    900: '#1B921D',
    A100: '#88FF90',
    A200: '#4DFF54',
    A400: '#1FFF2B',
    A700: '#00EA15'
  },
  indigo: {
    50: '#e8eaf6',
    100: '#c5cae9',
    200: '#A5DA9F',
    300: '#81CB79',
    400: '#65C05C',
    500: '#4AB53F',
    600: '#43AB39',
    700: '#3A9F30',
    800: '#319328',
    900: '#217E1A',
    A100: '#97FF8C',
    A200: '#63FE53',
    A400: '#4FFE3D',
    A700: '#43FE30'
  },
  blue: {
    50: '#e3f2fd',
    100: '#C9FBBB',
    200: '#A7F990',
    300: '#84F664',
    400: '#6AF542',
    500: '#88ff80',
    600: '#49E51E',
    700: '#3FD219',
    800: '#36C015',
    900: '#26A10D',
    A100: '#97FF82',
    A200: '#63FF44',
    A400: '#4CFF29',
    A700: '#45FF29'
  },
  'light-blue': {
    50: '#e1f5fe',
    100: '#C6FCB3',
    200: '#A1FA81',
    300: '#7CF74F',
    400: '#5FF629',
    500: '#43F403',
    600: '#3EE503',
    700: '#36D102',
    800: '#30BD02',
    900: '#239B01',
    A100: '#A2FF80',
    A200: '#73FF40',
    A400: '#44FF00',
    A700: '#39EA00'
  },
  cyan: {
    50: '#e0f7fa',
    100: '#C7F2B2',
    200: '#A3EA80',
    300: '#7DE14D',
    400: '#61DA26',
    500: '#45D400',
    600: '#40C100',
    700: '#38A700',
    800: '#308F00',
    900: '#236400',
    A100: '#B1FF84',
    A200: '#6CFF18',
    A400: '#54FF00',
    A700: '#44D400'
  },
  teal: {
    50: '#e0f2f1',
    100: '#C4DFB2',
    200: '#9DCB80',
    300: '#76B64D',
    400: '#58A626',
    500: '#3B9600',
    600: '#368900',
    700: '#307900',
    800: '#2A6900',
    900: '#004d40',
    A100: '#a7ffeb',
    A200: '#64ffda',
    A400: '#1de9b6',
    A700: '#4EBF00'
  },
  green: {
    50: '#e8f5e9',
    100: '#c8e6c9',
    200: '#a5d6a7',
    300: '#81c784',
    400: '#66bb6a',
    500: '#4caf50',
    600: '#43a047',
    700: '#388e3c',
    800: '#2e7d32',
    900: '#1b5e20',
    A100: '#b9f6ca',
    A200: '#69f0ae',
    A400: '#00e676',
    A700: '#00c853'
  },
  'light-green': {
    50: '#f1f8e9',
    100: '#dcedc8',
    200: '#c5e1a5',
    300: '#aed581',
    400: '#9ccc65',
    500: '#8bc34a',
    600: '#7cb342',
    700: '#689f38',
    800: '#558b2f',
    900: '#33691e',
    A100: '#ccff90',
    A200: '#b2ff59',
    A400: '#76ff03',
    A700: '#64dd17'
  },
  lime: {
    50: '#f9fbe7',
    100: '#f0f4c3',
    200: '#e6ee9c',
    300: '#dce775',
    400: '#d4e157',
    500: '#cddc39',
    600: '#c0ca33',
    700: '#afb42b',
    800: '#9e9d24',
    900: '#827717',
    A100: '#f4ff81',
    A200: '#eeff41',
    A400: '#c6ff00',
    A700: '#aeea00'
  },
  yellow: {
    50: '#fffde7',
    100: '#fff9c4',
    200: '#fff59d',
    300: '#fff176',
    400: '#ffee58',
    500: '#ffeb3b',
    600: '#fdd835',
    700: '#fbc02d',
    800: '#f9a825',
    900: '#f57f17',
    A100: '#ffff8d',
    A200: '#ffff00',
    A400: '#ffea00',
    A700: '#ffd600'
  },
  amber: {
    50: '#fff8e1',
    100: '#ffecb3',
    200: '#ffe082',
    300: '#ffd54f',
    400: '#ffca28',
    500: '#ffc107',
    600: '#ffb300',
    700: '#ffa000',
    800: '#ff8f00',
    900: '#ff6f00',
    A100: '#ffe57f',
    A200: '#ffd740',
    A400: '#ffc400',
    A700: '#ffab00'
  },
  orange: {
    50: '#fff3e0',
    100: '#ffe0b2',
    200: '#ffcc80',
    300: '#ffb74d',
    400: '#ffa726',
    500: '#ff9800',
    600: '#fb8c00',
    700: '#f57c00',
    800: '#ef6c00',
    900: '#e65100',
    A100: '#ffd180',
    A200: '#ffab40',
    A400: '#ff9100',
    A700: '#ff6d00'
  },
  'deep-orange': {
    50: '#fbe9e7',
    100: '#ffccbc',
    200: '#ffab91',
    300: '#ff8a65',
    400: '#ff7043',
    500: '#ff5722',
    600: '#f4511e',
    700: '#e64a19',
    800: '#d84315',
    900: '#bf360c',
    A100: '#ff9e80',
    A200: '#ff6e40',
    A400: '#ff3d00',
    A700: '#dd2c00'
  },
  brown: {
    50: '#efebe9',
    100: '#d7ccc8',
    200: '#bcaaa4',
    300: '#a1887f',
    400: '#8d6e63',
    500: '#795548',
    600: '#6d4c41',
    700: '#5d4037',
    800: '#4e342e',
    900: '#3e2723',
    A100: '#d7ccc8',
    A200: '#bcaaa4',
    A400: '#8d6e63',
    A700: '#5d4037'
  },
  grey: {
    50: '#fafafa',
    100: '#f5f5f5',
    200: '#eeeeee',
    300: '#e0e0e0',
    400: '#bdbdbd',
    500: '#9e9e9e',
    600: '#757575',
    700: '#616161',
    800: '#424242',
    900: '#212121',
    A100: '#ffffff',
    A200: '#000000',
    A400: '#303030',
    A700: '#616161'
  },
  'blue-grey': {
    50: '#eceff1',
    100: '#cfd8dc',
    200: '#b0bec5',
    300: '#90a4ae',
    400: '#819C78',
    500: '#6B8B60',
    600: '#5E7A54',
    700: '#4D6445',
    800: '#3D4F37',
    900: '#2B3826',
    A100: '#cfd8dc',
    A200: '#b0bec5',
    A400: '#819C78',
    A700: '#4D6445'
  }
};

export const materialColors = new Array<MaterialColorItem>();

const colorPalettes = ['blue', 'green', 'red', 'amber', 'blue-grey', 'purple', 'light-green',
  'indigo', 'pink', 'yellow', 'light-blue', 'orange', 'deep-purple', 'lime', 'teal', 'brown', 'cyan', 'deep-orange', 'grey'];
const colorSpectrum = ['500', 'A700', '600', '700', '800', '900', '300', '400', 'A200', 'A400'];

for (const key of Object.keys(materialColorPalette)) {
  const value = materialColorPalette[key];
  for (const label of Object.keys(value)) {
    if (colorSpectrum.indexOf(label) > -1) {
      const colorValue = value[label];
      const color = tinycolor(colorValue);
      const isDark = color.isDark();
      const colorItem = {
        value: color.toHexString(),
        group: key,
        label,
        isDark
      };
      materialColors.push(colorItem);
    }
  }
}

materialColors.sort((colorItem1, colorItem2) => {
  const spectrumIndex1 = colorSpectrum.indexOf(colorItem1.label);
  const spectrumIndex2 = colorSpectrum.indexOf(colorItem2.label);
  let result = spectrumIndex1 - spectrumIndex2;
  if (result === 0) {
    const paletteIndex1 = colorPalettes.indexOf(colorItem1.group);
    const paletteIndex2 = colorPalettes.indexOf(colorItem2.group);
    result = paletteIndex1 - paletteIndex2;
  }
  return result;
});
